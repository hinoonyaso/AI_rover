/* 한글: micro-ROS 노드 구현. 다른 태스크는 rcl을 직접 호출하지 않고 큐로 텔레메트리를 넘긴다. 에이전트 연결 상태기계(대기→연결→끊김→재연결)이며, 끊겨도 MCU는 계속 동작하고 cmd_vel이 끊기면 명령 timeout이 바퀴를 세운다. IMU는 base_node와 같은 회전(x=-ay, y=-ax, z=-az)으로 REP-103 프레임으로 변환한다. */
#include "comm_microros.h"

#include <math.h>
#include <rcl/error_handling.h>
#include <rcl/rcl.h>
#include <rclc/executor.h>
#include <rclc/rclc.h>
#include <rmw_microros/rmw_microros.h>
#include <std_msgs/msg/float32_multi_array.h>
#include <std_msgs/msg/int32_multi_array.h>
#include <std_msgs/msg/u_int16_multi_array.h>
#include <sensor_msgs/msg/battery_state.h>
#include <sensor_msgs/msg/imu.h>
#include <geometry_msgs/msg/twist.h>
#include <std_srvs/srv/set_bool.h>
#include <string.h>

#include "FreeRTOS.h"
#include "app.h"
#include "queue.h"
#include "task.h"

void microros_set_allocators(void);
void microros_transport_init(void);

#define G_MPS2 9.80665f
#define DEG2RAD 0.01745329252f

/* ---------- telemetry hand-off from other tasks (never call rcl from them) ---------- */
typedef enum { T_IMU, T_BATTERY, T_STATUS, T_WHEEL } tele_type_t;
typedef struct {
    tele_type_t type;
    union {
        struct { float a[3], g[3]; } imu;
        uint16_t mv;
        rrc_ext_status_t status;
        rrc_ext_wheel_t wheel;
    } u;
} tele_t;

static StaticQueue_t g_q_buf;
static uint8_t g_q_store[16 * sizeof(tele_t)];
static QueueHandle_t g_q;

static void tele_put(const tele_t *t)
{
    if (g_q) {
        (void)xQueueSend(g_q, t, 0); /* drop when full: telemetry is best effort */
    }
}

void comm_microros_publish_imu(const float a[3], const float g[3])
{
    tele_t t = {.type = T_IMU};
    memcpy(t.u.imu.a, a, sizeof(t.u.imu.a));
    memcpy(t.u.imu.g, g, sizeof(t.u.imu.g));
    tele_put(&t);
}

void comm_microros_publish_battery(uint16_t mv)
{
    tele_t t = {.type = T_BATTERY};
    t.u.mv = mv;
    tele_put(&t);
}

void comm_microros_publish_status(const rrc_ext_status_t *s)
{
    tele_t t = {.type = T_STATUS};
    t.u.status = *s;
    tele_put(&t);
}

void comm_microros_publish_wheel(const rrc_ext_wheel_t *w)
{
    tele_t t = {.type = T_WHEEL};
    t.u.wheel = *w;
    tele_put(&t);
}

/* ---------- entities ---------- */
static rcl_allocator_t g_alloc;
static rclc_support_t g_support;
static rcl_node_t g_node;
static rclc_executor_t g_exec;

static rcl_publisher_t pub_imu, pub_batt, pub_wheel, pub_status;
static rcl_subscription_t sub_cmd, sub_pid, sub_buzzer, sub_led;
static rcl_service_t srv_estop;

static sensor_msgs__msg__Imu m_imu;
static sensor_msgs__msg__BatteryState m_batt;
static std_msgs__msg__Float32MultiArray m_wheel, m_pid;
static std_msgs__msg__Int32MultiArray m_status;
static std_msgs__msg__UInt16MultiArray m_buzzer, m_led;
static geometry_msgs__msg__Twist m_cmd;
static std_srvs__srv__SetBool_Request m_estop_req;
static std_srvs__srv__SetBool_Response m_estop_res;

static char g_imu_frame[] = "imu_link";
static char g_batt_frame[] = "battery";
static float g_wheel_data[4], g_pid_data[4];
static int32_t g_status_data[10];
static uint16_t g_buzzer_data[4], g_led_data[3];
static char g_estop_msg[24];

/* telemetry/cleanup calls whose failure is handled by the agent-state machine */
#define RC_IGNORE(x) do { rcl_ret_t rc_ = (x); (void)rc_; } while (0)
#define CHECK_RC(x) do { if ((x) != RCL_RET_OK) { return false; } } while (0)

static void stamp(builtin_interfaces__msg__Time *t)
{
    const int64_t ns = rmw_uros_epoch_nanos();
    t->sec = (int32_t)(ns / 1000000000LL);
    t->nanosec = (uint32_t)(ns % 1000000000LL);
}

/* ---------- subscriptions: map to the common control API only ---------- */
/* Non-finite values are passed through: robot_set_velocity() drops the whole command (it used to turn
 * NaN into 0 and Inf into the full speed limit here). 한글: NaN/Inf는 그대로 넘겨 코어가 명령 전체를 버린다. */
static float clampf(float v, float lim)
{
    if (!isfinite(v)) {
        return v;
    }
    return v > lim ? lim : (v < -lim ? -lim : v);
}

/* 한글: /cmd_vel 수신: NaN/과속은 CMD_VEL_MAX_*로 제한한 뒤 robot_set_velocity()로만 전달한다(모터 직접 접근 없음). */
static void on_cmd_vel(const void *msg)
{
    const geometry_msgs__msg__Twist *t = msg;
    robot_set_velocity(&g_app.robot, clampf((float)t->linear.x, CMD_VEL_MAX_LINEAR_MPS),
                       clampf((float)t->linear.y, CMD_VEL_MAX_LINEAR_MPS),
                       clampf((float)t->angular.z, CMD_VEL_MAX_ANGULAR_RPS), app_now_ms(), ROBOT_SRC_MICROROS);
}

static void on_pid(const void *msg)
{
    const std_msgs__msg__Float32MultiArray *m = msg;
    if (m->data.size >= 4 && g_app.svc.set_pid) {
        g_app.svc.set_pid(g_app.svc.hw, (uint8_t)m->data.data[0], m->data.data[1], m->data.data[2], m->data.data[3]);
    }
}

static void on_buzzer(const void *msg)
{
    const std_msgs__msg__UInt16MultiArray *m = msg;
    if (m->data.size >= 4 && g_app.svc.buzzer_set) {
        g_app.svc.buzzer_set(g_app.svc.hw, m->data.data[0], m->data.data[1], m->data.data[2], m->data.data[3]);
    }
}

static void on_led(const void *msg)
{
    const std_msgs__msg__UInt16MultiArray *m = msg;
    if (m->data.size >= 3 && g_app.svc.led_set) {
        g_app.svc.led_set(g_app.svc.hw, 0, m->data.data[0], m->data.data[1], m->data.data[2]);
    }
}

static void on_estop(const void *req, void *res)
{
    const std_srvs__srv__SetBool_Request *rq = req;
    std_srvs__srv__SetBool_Response *rs = res;
    if (rq->data) {
        robot_estop(&g_app.robot);
    } else {
        robot_clear_estop(&g_app.robot);
    }
    rs->success = true;
    rs->message.data = g_estop_msg;
    rs->message.size = (size_t)snprintf(g_estop_msg, sizeof(g_estop_msg), rq->data ? "estop latched" : "estop cleared");
    rs->message.capacity = sizeof(g_estop_msg);
}

static void init_messages(void)
{
    sensor_msgs__msg__Imu__init(&m_imu);
    m_imu.header.frame_id.data = g_imu_frame;
    m_imu.header.frame_id.size = sizeof(g_imu_frame) - 1;
    m_imu.header.frame_id.capacity = sizeof(g_imu_frame);
    m_imu.orientation_covariance[0] = -1.0; /* no orientation estimate (REP-145) */
    m_imu.linear_acceleration_covariance[0] = 0.0004;
    m_imu.linear_acceleration_covariance[4] = 0.0004;
    m_imu.linear_acceleration_covariance[8] = 0.004;
    m_imu.angular_velocity_covariance[0] = 0.01;
    m_imu.angular_velocity_covariance[4] = 0.01;
    m_imu.angular_velocity_covariance[8] = 0.01;

    sensor_msgs__msg__BatteryState__init(&m_batt);
    m_batt.header.frame_id.data = g_batt_frame;
    m_batt.header.frame_id.size = sizeof(g_batt_frame) - 1;
    m_batt.header.frame_id.capacity = sizeof(g_batt_frame);
    m_batt.power_supply_status = sensor_msgs__msg__BatteryState__POWER_SUPPLY_STATUS_DISCHARGING;
    m_batt.power_supply_technology = sensor_msgs__msg__BatteryState__POWER_SUPPLY_TECHNOLOGY_LIPO;
    m_batt.present = true;
    m_batt.current = NAN;
    m_batt.charge = NAN;
    m_batt.capacity = NAN;
    m_batt.design_capacity = NAN;
    m_batt.percentage = NAN;

    std_msgs__msg__Float32MultiArray__init(&m_wheel);
    m_wheel.data.data = g_wheel_data;
    m_wheel.data.size = 4;
    m_wheel.data.capacity = 4;
    std_msgs__msg__Float32MultiArray__init(&m_pid);
    m_pid.data.data = g_pid_data;
    m_pid.data.size = 0;
    m_pid.data.capacity = 4;
    std_msgs__msg__Int32MultiArray__init(&m_status);
    m_status.data.data = g_status_data;
    m_status.data.size = 10;
    m_status.data.capacity = 10;
    std_msgs__msg__UInt16MultiArray__init(&m_buzzer);
    m_buzzer.data.data = g_buzzer_data;
    m_buzzer.data.size = 0;
    m_buzzer.data.capacity = 4;
    std_msgs__msg__UInt16MultiArray__init(&m_led);
    m_led.data.data = g_led_data;
    m_led.data.size = 0;
    m_led.data.capacity = 3;
    geometry_msgs__msg__Twist__init(&m_cmd);
    std_srvs__srv__SetBool_Request__init(&m_estop_req);
    std_srvs__srv__SetBool_Response__init(&m_estop_res);
}

/* 한글: 노드/퍼블리셔/구독/서비스/익스큐터 생성. 센서 토픽은 best-effort, 상태/배터리는 reliable. */
static bool create_entities(void)
{
    g_alloc = rcl_get_default_allocator();
    CHECK_RC(rclc_support_init(&g_support, 0, NULL, &g_alloc));
    CHECK_RC(rclc_node_init_default(&g_node, "rrc_m4", "", &g_support));

    CHECK_RC(rclc_publisher_init_best_effort(&pub_imu, &g_node, ROSIDL_GET_MSG_TYPE_SUPPORT(sensor_msgs, msg, Imu), "rrc/imu_raw"));
    CHECK_RC(rclc_publisher_init_default(&pub_batt, &g_node, ROSIDL_GET_MSG_TYPE_SUPPORT(sensor_msgs, msg, BatteryState), "rrc/battery"));
    CHECK_RC(rclc_publisher_init_best_effort(&pub_wheel, &g_node, ROSIDL_GET_MSG_TYPE_SUPPORT(std_msgs, msg, Float32MultiArray), "rrc/wheel_rps"));
    CHECK_RC(rclc_publisher_init_default(&pub_status, &g_node, ROSIDL_GET_MSG_TYPE_SUPPORT(std_msgs, msg, Int32MultiArray), "rrc/status"));

    CHECK_RC(rclc_subscription_init_best_effort(&sub_cmd, &g_node, ROSIDL_GET_MSG_TYPE_SUPPORT(geometry_msgs, msg, Twist), "cmd_vel"));
    CHECK_RC(rclc_subscription_init_default(&sub_pid, &g_node, ROSIDL_GET_MSG_TYPE_SUPPORT(std_msgs, msg, Float32MultiArray), "rrc/pid_cmd"));
    CHECK_RC(rclc_subscription_init_default(&sub_buzzer, &g_node, ROSIDL_GET_MSG_TYPE_SUPPORT(std_msgs, msg, UInt16MultiArray), "rrc/buzzer_cmd"));
    CHECK_RC(rclc_subscription_init_default(&sub_led, &g_node, ROSIDL_GET_MSG_TYPE_SUPPORT(std_msgs, msg, UInt16MultiArray), "rrc/led_cmd"));
    CHECK_RC(rclc_service_init_default(&srv_estop, &g_node, ROSIDL_GET_SRV_TYPE_SUPPORT(std_srvs, srv, SetBool), "rrc/estop"));

    CHECK_RC(rclc_executor_init(&g_exec, &g_support.context, 5, &g_alloc));
    CHECK_RC(rclc_executor_add_subscription(&g_exec, &sub_cmd, &m_cmd, on_cmd_vel, ON_NEW_DATA));
    CHECK_RC(rclc_executor_add_subscription(&g_exec, &sub_pid, &m_pid, on_pid, ON_NEW_DATA));
    CHECK_RC(rclc_executor_add_subscription(&g_exec, &sub_buzzer, &m_buzzer, on_buzzer, ON_NEW_DATA));
    CHECK_RC(rclc_executor_add_subscription(&g_exec, &sub_led, &m_led, on_led, ON_NEW_DATA));
    CHECK_RC(rclc_executor_add_service(&g_exec, &srv_estop, &m_estop_req, &m_estop_res, on_estop));

    (void)rmw_uros_sync_session(500); /* time sync for header stamps; non-fatal */
    return true;
}

static void destroy_entities(void)
{
    rmw_context_t *ctx = rcl_context_get_rmw_context(&g_support.context);
    (void)rmw_uros_set_context_entity_destroy_session_timeout(ctx, 0);
    RC_IGNORE(rcl_publisher_fini(&pub_imu, &g_node));
    RC_IGNORE(rcl_publisher_fini(&pub_batt, &g_node));
    RC_IGNORE(rcl_publisher_fini(&pub_wheel, &g_node));
    RC_IGNORE(rcl_publisher_fini(&pub_status, &g_node));
    RC_IGNORE(rcl_subscription_fini(&sub_cmd, &g_node));
    RC_IGNORE(rcl_subscription_fini(&sub_pid, &g_node));
    RC_IGNORE(rcl_subscription_fini(&sub_buzzer, &g_node));
    RC_IGNORE(rcl_subscription_fini(&sub_led, &g_node));
    RC_IGNORE(rcl_service_fini(&srv_estop, &g_node));
    (void)rclc_executor_fini(&g_exec);
    RC_IGNORE(rcl_node_fini(&g_node));
    (void)rclc_support_fini(&g_support);
}

static void publish_tele(const tele_t *t)
{
    switch (t->type) {
    case T_IMU: {
        /* board frame (X right, Y back, Z down) -> REP-103 (x fwd, y left, z up): same rotation as base_node */
        stamp(&m_imu.header.stamp);
        m_imu.linear_acceleration.x = -t->u.imu.a[1] * G_MPS2;
        m_imu.linear_acceleration.y = -t->u.imu.a[0] * G_MPS2;
        m_imu.linear_acceleration.z = -t->u.imu.a[2] * G_MPS2;
        m_imu.angular_velocity.x = -t->u.imu.g[1] * DEG2RAD;
        m_imu.angular_velocity.y = -t->u.imu.g[0] * DEG2RAD;
        m_imu.angular_velocity.z = -t->u.imu.g[2] * DEG2RAD;
        RC_IGNORE(rcl_publish(&pub_imu, &m_imu, NULL));
        break;
    }
    case T_BATTERY:
        stamp(&m_batt.header.stamp);
        m_batt.voltage = (float)t->u.mv / 1000.0f;
        RC_IGNORE(rcl_publish(&pub_batt, &m_batt, NULL));
        break;
    case T_WHEEL:
        for (int i = 0; i < 4; i++) {
            g_wheel_data[i] = t->u.wheel.rps[i];
        }
        RC_IGNORE(rcl_publish(&pub_wheel, &m_wheel, NULL));
        break;
    case T_STATUS: {
        const rrc_ext_status_t *s = &t->u.status;
        g_status_data[0] = s->flags;
        g_status_data[1] = s->stop_reason;
        g_status_data[2] = s->imu_kind;
        g_status_data[3] = s->comm_mode;
        for (int i = 0; i < 4; i++) {
            g_status_data[4 + i] = s->motor_fault[i];
        }
        g_status_data[8] = (int32_t)s->uptime_ms;
        g_status_data[9] = (int32_t)s->reset_cause;
        RC_IGNORE(rcl_publish(&pub_status, &m_status, NULL));
        break;
    }
    }
}

typedef enum { WAITING_AGENT, AGENT_AVAILABLE, AGENT_CONNECTED, AGENT_DISCONNECTED } agent_state_t;

/* 한글: 에이전트 연결 상태기계. 연결 중 1초마다 ping, 실패하면 엔티티를 정리하고 재연결한다. */
void comm_microros_task(void *arg)
{
    (void)arg;
    agent_state_t state = WAITING_AGENT;
    TickType_t last_ping = 0;
    tele_t t;

    g_q = xQueueCreateStatic(16, sizeof(tele_t), g_q_store, &g_q_buf);
    microros_set_allocators();
    microros_transport_init();
    init_messages();

    for (;;) {
        switch (state) {
        case WAITING_AGENT:
            vTaskDelay(pdMS_TO_TICKS(200));
            if (rmw_uros_ping_agent(100, 1) == RMW_RET_OK) {
                state = AGENT_AVAILABLE;
            }
            break;
        case AGENT_AVAILABLE:
            state = create_entities() ? AGENT_CONNECTED : AGENT_DISCONNECTED;
            if (state == AGENT_DISCONNECTED) {
                destroy_entities();
            }
            last_ping = xTaskGetTickCount();
            break;
        case AGENT_CONNECTED:
            (void)rclc_executor_spin_some(&g_exec, RCL_MS_TO_NS(2));
            while (xQueueReceive(g_q, &t, 0) == pdTRUE) {
                publish_tele(&t);
            }
            if (xTaskGetTickCount() - last_ping > pdMS_TO_TICKS(1000)) {
                last_ping = xTaskGetTickCount();
                if (rmw_uros_ping_agent(100, 2) != RMW_RET_OK) {
                    state = AGENT_DISCONNECTED;
                }
            }
            vTaskDelay(1);
            break;
        case AGENT_DISCONNECTED:
            /* the MCU keeps running; the command timeout stops the wheels if cmd_vel stops */
            destroy_entities();
            while (xQueueReceive(g_q, &t, 0) == pdTRUE) {
            }
            state = WAITING_AGENT;
            break;
        }
    }
}

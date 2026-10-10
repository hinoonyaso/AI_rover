/* 한글: 빌드 설정. "추정(ASSUMED)"으로 표시된 값은 브링업에서 확인해야 한다(firmware_source/PINMAP.md). MOTOR_ENABLE 기본 0 = 모터 출력 금지. */
/* Build-time configuration. Everything here marked "ASSUMED" is documented in
 * firmware_source/PINMAP.md as 추정 and must be confirmed during bring-up (test plan item 7). */
#ifndef APP_CONFIG_H
#define APP_CONFIG_H

#define COMM_MODE_RRC 0
#define COMM_MODE_MICROROS 1
#ifndef COMM_MODE
#define COMM_MODE COMM_MODE_RRC
#endif

/* Motor outputs. 0 = every motor command is ignored and the H-bridge pins stay at 0 (L2 bring-up:
 * IMU/battery/comm only). Set to 1 only after the wheel polarity checks of the test plan. */
#ifndef MOTOR_ENABLE
#define MOTOR_ENABLE 0
#endif

/* Local (MCU-side) driving from Bluetooth app / USB gamepad / SBUS. Off by default: the host owns
 * motion; these are vendor features kept for standalone operation. */
#ifndef LOCAL_DRIVE_ENABLE
#define LOCAL_DRIVE_ENABLE 0
#endif

#define PWM_SERVO_COUNT 4

#ifndef RRC_FREERTOS_HEAP_BYTES
#if COMM_MODE == COMM_MODE_MICROROS
#define RRC_FREERTOS_HEAP_BYTES (40 * 1024) /* rcl/rclc entities + serialisation buffers */
#else
#define RRC_FREERTOS_HEAP_BYTES (24 * 1024)
#endif
#endif

/* ---- kinematics: same numbers as src/jetrover_base/config/base.yaml ---- */
#define ROBOT_WHEELBASE_M 0.216f
#define ROBOT_TRACK_WIDTH_M 0.195f
#define ROBOT_WHEEL_DIAMETER_M 0.097f

/* ---- motor model: ASSUMED (Hiwonder JGB520 example values; not in the public docs) ---- */
#define MOTOR_TICKS_PER_CIRCLE 1320
#define MOTOR_RPS_LIMIT 5.0f
#define MOTOR_PID_KP 63.0f
#define MOTOR_PID_KI 2.6f
#define MOTOR_PID_KD 2.4f
#define MOTOR_ENCODER_TIM_OVERFLOW 60000
/* Encoder direction per motor (+1 / -1). */
/* 2026-10-10 bring-up (RAW_PWM, wheels lifted): with M2's PWM pair swapped (drv_motor.c) every encoder
 * counts up on a positive pulse -> all +1. (First try {1,1,-1,-1} was wrong for M3, and M2's -1 only
 * compensated its swapped pair.) A wrong sign is caught by the encoder-sign guard. troubleshooting/036.
 * 한글: M2 PWM 짝을 바로잡으니 4개 모두 +1. */
#define MOTOR_ENCODER_SIGN {1, 1, 1, 1}

/* ---- safety ---- */
#define CMD_TIMEOUT_MS 1000
#define LOW_BATTERY_CUTOFF_MV 9500
#define LOW_BATTERY_CLEAR_MV 10000
#define IWDG_TIMEOUT_MS 500

/* ---- IMU board-frame axis map: ASSUMED identity (see core/imu.h) ---- */
#define IMU_MAP_SRC {0, 1, 2}
#define IMU_MAP_SIGN {1, 1, 1}

/* ---- task rates ---- */
#define STATUS_PERIOD_MS 100
#define WHEEL_PERIOD_MS 20
#define BATTERY_PERIOD_MS 1000

#endif

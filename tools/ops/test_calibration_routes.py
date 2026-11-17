"""Verify bounded capture and candidate persistence. / 촬영 제한과 후보 보관을 검증한다."""
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch
from fastapi import HTTPException
import sys
sys.path.insert(0, str(Path(__file__).parent / 'backend'))
import calibration_routes as api


class CalibrationRoutesTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / 'run').mkdir()
        self.patches = [patch.object(api, 'ROOT', self.root), patch.object(api, 'capture_dir', self.root),
                        patch.object(api, 'state', {'running': None, 'error': None, 'imu': None, 'camera': None, 'captures': []})]
        for item in self.patches: item.start()

    def tearDown(self):
        for item in reversed(self.patches): item.stop()
        self.tmp.cleanup()

    def test_capture_missing_duplicate_and_reset(self):
        with self.assertRaises(HTTPException) as error: api.camera_capture()
        self.assertEqual(error.exception.detail, 'camera_unavailable')
        (self.root / 'run/camera-calibration.png').write_bytes(b'\x89PNG\r\n\x1a\ntest-frame')
        self.assertEqual(api.camera_capture()['captures'], 1)
        with self.assertRaises(HTTPException) as error: api.camera_capture()
        self.assertEqual(error.exception.detail, 'duplicate_frame')
        self.assertEqual(api.camera_reset()['captures'], 0)

    def test_history_details_and_candidate_restore_preserve_active_settings(self):
        first=api.save_result('imu', {'candidate':[1,2,3], 'current_bias':[0,0,0], 'applied':False})
        record_id=api.calibration_status()['history'][0]['id']
        api.save_result('imu', {'candidate':[4,5,6], 'applied':False})
        detail=api.calibration_history_detail(record_id)
        self.assertEqual(detail['result'],first)
        restored=api.restore_candidate(record_id)
        self.assertEqual(restored['imu']['candidate'],[1,2,3])
        self.assertEqual(restored['imu']['restored_from'],record_id)
        self.assertEqual(restored['imu']['original_measured_at'],first['measured_at'])
        self.assertTrue(restored['history'][0]['details_available'])
        with self.assertRaises(HTTPException): api.calibration_history_detail('../invalid')

    def test_candidate_is_separate_and_survives_state_reset(self):
        saved = api.save_result('imu', {'candidate': [1, 2, 3], 'applied': False})
        self.assertEqual(saved['candidate'], [1, 2, 3])
        self.assertEqual(api.calibration_status()['imu'], saved)
        self.assertEqual((self.root / 'calibration/candidates.json').stat().st_mode & 0o777, 0o600)

    def test_catalog_and_history_preserve_legacy_candidates(self):
        import json
        directory = self.root / 'calibration'
        directory.mkdir()
        legacy = {'imu': {'candidate': [1, 2, 3], 'applied': False}}
        (directory / 'candidates.json').write_text(json.dumps(legacy))
        before = api.calibration_status()
        self.assertEqual(before['history'], [])
        self.assertEqual(before['imu'], legacy['imu'])
        self.assertEqual(len(before['catalog']), 11)
        self.assertEqual(len({item['id'] for item in before['catalog']}), 11)
        self.assertEqual(sum(item['availability'] == 'candidate' for item in before['catalog']), 7)
        self.assertEqual(sum(item['availability'] == 'comparison' for item in before['catalog']), 3)
        self.assertEqual(sum(item['availability'] == 'record' for item in before['catalog']), 1)
        api.save_result('camera', {'applied': False, 'data': 'private-value'})
        api.save_result('imu', {'candidate': [4, 5, 6], 'applied': False})
        after = api.calibration_status()
        self.assertEqual([item['kind'] for item in after['history']], ['imu', 'camera'])
        self.assertNotIn('private-value', json.dumps(after['history']))
        self.assertEqual(after['camera']['data'], 'private-value')

    def test_footprint_candidate_preserves_asymmetry_and_active_settings(self):
        from pydantic import ValidationError
        data = api.FootprintMeasurement(front_cm=20, rear_cm=30, left_cm=15, right_cm=25)
        result = api.footprint_candidate(data)['footprint']
        self.assertEqual(result['polygon_m'], [[.2, .15], [.2, -.25], [-.3, -.25], [-.3, .15]])
        self.assertEqual(result['frame_id'], 'base_footprint')
        self.assertIsNone(result['safety_margin_included'])
        self.assertFalse(result['applied'])
        self.assertEqual(api.calibration_status()['history'][0]['kind'], 'footprint')
        for value in (0, -1, float('nan'), 301, True):
            with self.subTest(value=value), self.assertRaises(ValidationError):
                api.FootprintMeasurement(front_cm=value, rear_cm=30, left_cm=15, right_cm=25)

    def test_odom_recording_compares_continuous_stream(self):
        import json
        path=self.root/'run/ros-status.json'
        first={'x_m':0.,'y_m':0.,'yaw':0.,'yaw_unwrapped':0.,'stamp':10.,'received_at':99.,'frame_id':'odom','child_frame_id':'base_link','generation':'same'}
        with patch.object(api.time,'time',return_value=100.):
            path.write_text(json.dumps({'timestamp':99.5,'odometry':{'raw':first}}))
            api.odom_capture_start(api.OdomCaptureStart(motion='forward',source='raw'))
            end=dict(first,x_m=1.1,stamp=11.,received_at=99.9)
            path.write_text(json.dumps({'timestamp':99.9,'odometry':{'raw':end}}))
            result=api.odom_capture_finish(api.OdomCaptureFinish(reference=100.))['odometry']
            self.assertAlmostEqual(result['recorded'],110.)
            self.assertEqual(result['source'],'odom_raw')
            self.assertIsNone(api.calibration_status()['odom_capture'])

    def test_wheel_speed_comparison_requires_recent_feedback(self):
        import json
        path = self.root / 'run/ros-status.json'
        snapshot = {'timestamp':99.9, 'wheel_feedback':{'received_at':99.8,'port_rps':[1.,2.,-3.,-4.], 'port_counter':[1,2,3,4]}}
        with patch.object(api.time, 'time', return_value=100.):
            path.write_text(json.dumps(snapshot))
            result = api.wheel_speed_compare(api.WheelSpeedReference(port=3, reference_rps=-2.))['wheel_speed']
            self.assertEqual(result['sensor_rps'], -3.)
            self.assertEqual(result['difference_rps'], -1.)
            self.assertEqual(result['relative_error_percent'], -50.)
            snapshot['wheel_feedback']['received_at'] = 90.
            path.write_text(json.dumps(snapshot))
            with self.assertRaises(HTTPException) as error:
                api.wheel_speed_compare(api.WheelSpeedReference(port=1, reference_rps=1.))
            self.assertEqual(error.exception.detail, 'wheel_feedback_unavailable')
            with self.assertRaises(HTTPException) as error:
                api.wheel_speed_compare(api.WheelSpeedReference(port=1, reference_rps=0.))
            self.assertEqual(error.exception.detail, 'wheel_reference_too_small')

    def test_wheel_multi_reference_fit_and_stale_rejection(self):
        import json
        path=self.root/'run/ros-status.json'
        with patch.object(api.time,'time',return_value=100.):
            for index, speed in enumerate([.3,.6,1.]):
                snapshot={'timestamp':99.9,'wheel_feedback':{'received_at':99.1+index*.1,'port_rps':[speed,0.,0.,0.],'port_counter':[0,0,0,0]}}
                path.write_text(json.dumps(snapshot))
                api.wheel_speed_sample(api.WheelSpeedReference(port=1,reference_rps=speed*1.1))
            result=api.wheel_speed_fit()['wheel_speed_fit']
            self.assertAlmostEqual(result['scale'],1.1)
            self.assertLess(result['rms_rps'],1e-10)
            self.assertFalse(result['firmware_applied'])
            with self.assertRaises(HTTPException) as error:api.wheel_speed_sample(api.WheelSpeedReference(port=1,reference_rps=1.1))
            self.assertEqual(error.exception.detail,'wheel_duplicate_sample')

    def test_gripper_width_uses_fresh_observations_and_rejects_inverted_width(self):
        import json
        path = self.root / 'run/ros-status.json'
        joint = {'position_rad': 1.0, 'servo_id': 10, 'joint_message_age_s':0.1, 'servo_response_age_s':0.2}
        snapshot = {'timestamp':99.9, 'arm':{'mapping_confirmed':True,'source_confirmed':True,'joints':{'r_joint':joint}}}
        with patch.object(api.time, 'time', return_value=100.):
            path.write_text(json.dumps(snapshot))
            api.gripper_width_sample(api.GripperWidthSample(phase='open', width_mm=40))
            joint['position_rad'] = 0.5
            path.write_text(json.dumps(snapshot))
            with self.assertRaises(HTTPException) as error:
                api.gripper_width_sample(api.GripperWidthSample(phase='closed', width_mm=50))
            self.assertEqual(error.exception.detail, 'gripper_sample_invalid')
            result = api.gripper_width_sample(api.GripperWidthSample(phase='closed', width_mm=10))['gripper_width']
            self.assertEqual(result['slope_mm_per_rad'], 60)
            self.assertFalse(result['applied'])
            snapshot['arm']['source_confirmed'] = False
            path.write_text(json.dumps(snapshot))
            with self.assertRaises(HTTPException) as error:
                api.gripper_width_sample(api.GripperWidthSample(phase='open', width_mm=40))
            self.assertEqual(error.exception.detail, 'joint_unavailable')
            api.gripper_width_reset()
            self.assertEqual(api.calibration_status()['gripper_width_samples'], {})
            self.assertIsNotNone(api.calibration_status()['gripper_width'])

    def test_pose_workers_reject_invalid_geometry(self):
        identity = [[1.,0.,0.,0.],[0.,1.,0.,0.],[0.,0.,1.,0.],[0.,0.,0.,1.]]
        with self.assertRaises(HTTPException) as error:
            api.tcp_pivot_fit(api.TcpPivotMeasurement(poses=[identity]*5))
        self.assertEqual(error.exception.detail, 'insufficient_pose_diversity')
        pair = api.HandEyePair(base_T_link4=identity, camera_T_target=identity)
        with self.assertRaises(HTTPException) as error:
            api.hand_eye_fit(api.HandEyeMeasurement(pairs=[pair]*5))
        self.assertEqual(error.exception.detail, 'insufficient_rotation_diversity')

    def test_hand_eye_settings_route_applies_reviewed_candidate_and_restores(self):
        target = self.root / 'install/jetrover_description/share/jetrover_description/urdf/depth_camera.urdf.xacro'
        target.parent.mkdir(parents=True)
        original = (Path(__file__).resolve().parents[2] / 'src/jetrover_description/urdf/depth_camera.urdf.xacro').read_bytes()
        target.write_bytes(original)
        mount = [[1.,0.,0.,.1],[0.,1.,0.,.2],[0.,0.,1.,.3],[0.,0.,0.,1.]]
        api.state['hand_eye'] = {'applied':False, 'parent_frame':'link4', 'camera_frame':'depth_cam_color_optical_frame',
                                 'link4_T_camera':[[1.,0.,0.,.2],[0.,1.,0.,.4],[0.,0.,1.,.6],[0.,0.,0.,1.]]}
        with patch.object(api, 'PROJECT', self.root), patch.object(api, '_camera_mount_transform', return_value=mount):
            preview = api.hand_eye_settings_status()['preview']
            applied = api.hand_eye_settings_apply(api.GyroApply(config_hash=preview['config_hash'], candidate_hash=preview['candidate_hash']))
            self.assertNotEqual(target.read_bytes(), original)
            self.assertTrue(api.hand_eye_settings_status()['backups'])
            api.hand_eye_settings_restore(api.GyroRestore(backup_id=applied['backup_id']))
            self.assertEqual(target.read_bytes(), original)

    def test_lidar_yaw_candidate_apply_and_restore_routes(self):
        target = self.root / 'install/jetrover_description/share/jetrover_description/urdf/lidar.urdf.xacro'
        target.parent.mkdir(parents=True)
        original = (Path(__file__).resolve().parents[2]/'src/jetrover_description/urdf/lidar.urdf.xacro').read_bytes()
        target.write_bytes(original)
        with patch.object(api, 'PROJECT', self.root):
            result = api.lidar_yaw_candidate(api.LidarYawMeasurement(yaw_deg=12.0))
            self.assertFalse(result['lidar_yaw']['applied'])
            preview = api.lidar_yaw_settings_status()['preview']
            applied = api.lidar_yaw_settings_apply(api.GyroApply(config_hash=preview['config_hash'],candidate_hash=preview['candidate_hash']))
            self.assertNotEqual(target.read_bytes(), original)
            api.lidar_settings_restore(api.GyroRestore(backup_id=applied['backup_id']))
            self.assertEqual(target.read_bytes(), original)

    def test_registration_mode_route_applies_and_restores_temporary_config(self):
        target=self.root/'install/jetrover_perception/share/jetrover_perception/config/dabai_dcw.yaml'
        target.parent.mkdir(parents=True)
        original=(Path(__file__).resolve().parents[2]/'src/jetrover_perception/config/dabai_dcw.yaml').read_bytes()
        target.write_bytes(original)
        with patch.object(api,'PROJECT',self.root):
            plan=api.rgb_depth_settings_status('SW_D2C')['preview']
            request=api.RegistrationApply(mode='SW_D2C',config_hash=plan['config_hash'],candidate_hash=plan['candidate_hash'])
            result=api.rgb_depth_settings_apply(request)
            self.assertEqual(api.rgb_depth_settings_status('SW_D2C')['preview']['current'],'SW_D2C')
            api.rgb_depth_settings_restore(api.GyroRestore(backup_id=result['backup_id']))
            self.assertEqual(target.read_bytes(),original)

    def test_hand_eye_capture_requires_fresh_stationary_arm(self):
        import json
        from types import SimpleNamespace
        identity=[[1.,0.,0.,0.],[0.,1.,0.,0.],[0.,0.,1.,0.],[0.,0.,0.,1.]]
        arm={'source_confirmed':True,'joints':{f'joint{i}':{'fresh':True,'position_rad':0.} for i in range(1,6)}}
        completed=SimpleNamespace(returncode=0,stdout=json.dumps({'result':{'base_T_link4':identity,'camera_T_target':identity}}))
        with patch.object(api,'public_state',return_value={'arm_info':arm}),patch.object(api.subprocess,'run',return_value=completed):
            data=api.hand_eye_capture(api.Board(columns=7,rows=6,square_mm=25))
            self.assertEqual(data['result']['base_T_link4'],identity)
            arm['source_confirmed']=False
            with self.assertRaises(HTTPException) as error:api.hand_eye_capture(api.Board(columns=7,rows=6,square_mm=25))
            self.assertEqual(error.exception.detail,'arm_feedback_unavailable')

    def test_tcp_capture_requires_fresh_real_feedback_and_rejects_motion(self):
        from types import SimpleNamespace
        joints = {f'joint{i}': {'fresh':True, 'position_rad':0.0} for i in range(1, 6)}
        arm = {'source_confirmed':True, 'joints':joints}
        pose = [[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]]
        completed = SimpleNamespace(returncode=0, stdout=__import__('json').dumps({'result':pose,'stamp':10.0}))
        with patch.object(api, 'public_state', return_value={'arm_info':arm}), patch.object(api.subprocess, 'run', return_value=completed):
            self.assertEqual(api.tcp_pivot_capture()['pose'], pose)
            joints['joint1']['fresh'] = False
            with self.assertRaises(HTTPException) as error: api.tcp_pivot_capture()
            self.assertEqual(error.exception.detail, 'arm_feedback_unavailable')
        joints['joint1']['fresh'] = True
        moving = {'source_confirmed':True, 'joints':{**joints, 'joint1':{'fresh':True,'position_rad':.1}}}
        with patch.object(api, 'public_state', side_effect=[{'arm_info':arm}, {'arm_info':moving}]), patch.object(api.subprocess, 'run', return_value=completed):
            with self.assertRaises(HTTPException) as error: api.tcp_pivot_capture()
            self.assertEqual(error.exception.detail, 'arm_moved')

    def test_depth_source_requires_matching_corrected_background(self):
        import hashlib
        import json
        directory=self.root/'calibration';background=directory/'backgrounds'/('a'*32+'.npy')
        background.parent.mkdir(parents=True);background.write_bytes(b'image')
        calibration=directory/'rgbd-extrinsic-active.json';calibration.write_bytes(b'calibration')
        with self.assertRaises(HTTPException):api.depth_source_select(api.DepthSourceSelection(source='corrected',background_id='a'*32))
        metadata={'source_topic':'/depth_cam/depth_corrected/image_raw','background_sha256':hashlib.sha256(b'image').hexdigest(),'calibration_sha256':hashlib.sha256(b'calibration').hexdigest()}
        background.with_suffix('.npy.json').write_text(json.dumps(metadata))
        result=api.depth_source_select(api.DepthSourceSelection(source='corrected',background_id='a'*32))
        self.assertTrue(result['requires_restart']);self.assertEqual(api.depth_source_status()['background_id'],'a'*32)
        calibration.write_bytes(b'changed')
        with self.assertRaises(HTTPException):api.depth_source_select(api.DepthSourceSelection(source='corrected',background_id='a'*32))
        self.assertEqual(api.depth_source_select(api.DepthSourceSelection(source='default'))['source'],'default')

    def test_rgbd_extrinsic_fit_keeps_device_unchanged(self):
        pairs=[]
        for x,y,z in [(0,0,0),(1,0,0),(0,1,0),(0,0,1)]:
            pairs.append(api.ExtrinsicPair(camera=api.Point3(x=x,y=y,z=z),reference=api.Point3(x=x+.1,y=y,z=z)))
        result=api.rgb_depth_extrinsic_fit(api.RgbdExtrinsicMeasurement(pairs=pairs))['rgbd_extrinsic']
        self.assertAlmostEqual(result['translation_m'][0],.1)
        self.assertEqual(result['source_frame'],'depth_cam_depth_optical_frame')
        self.assertFalse(result['device_applied'])

    def test_extrinsic_fit_recovers_transform_and_rejects_collinear_points(self):
        def pair(x, y, z):
            return api.ExtrinsicPair(camera=api.Point3(x=x,y=y,z=z), reference=api.Point3(x=-y+1,y=x+2,z=z+3))
        data = api.ExtrinsicMeasurement(reference_frame='base_link', pairs=[pair(0,0,0),pair(1,0,0),pair(0,1,0),pair(0,0,1)])
        result = api.extrinsic_fit(data)['tcp']
        self.assertLess(result['rms_m'], 1e-10)
        for actual, expected in zip(result['translation_m'], [1,2,3]): self.assertAlmostEqual(actual, expected)
        self.assertFalse(result['hand_eye_calibrated'])
        self.assertFalse(result['applied'])
        invalid = api.ExtrinsicMeasurement(reference_frame='base_link', pairs=[pair(i,0,0) for i in range(4)])
        with self.assertRaises(HTTPException) as error: api.extrinsic_fit(invalid)
        self.assertEqual(error.exception.detail, 'degenerate_points')

    def test_joint_candidate_requires_confirmed_source_and_bounded_correction(self):
        api.state['arm']={'joint':'joint1','source_confirmed':True,'current_offset_rad':.1,'difference_rad':.05,
                          'reference_rad':0.,'observed_rad':.05,'applied':False}
        result=api.joint_offset_candidate(api.JointCandidateRequest(joint='joint1'))['joint_candidate']
        self.assertAlmostEqual(result['candidate_offset_rad'],.05)
        api.state['arm']['source_confirmed']=False
        with self.assertRaises(HTTPException) as error:api.joint_offset_candidate(api.JointCandidateRequest(joint='joint1'))
        self.assertEqual(error.exception.detail,'joint_reference_unconfirmed')
        api.state['arm']['source_confirmed']=True;api.state['arm']['difference_rad']=.5
        with self.assertRaises(HTTPException) as error:api.joint_offset_candidate(api.JointCandidateRequest(joint='joint1'))
        self.assertEqual(error.exception.detail,'joint_correction_out_of_range')

    def test_joint_comparison_requires_fresh_servo_response(self):
        import json
        path = self.root / 'run/ros-status.json'
        joint = {'position_rad': 0.2, 'servo_id': 1, 'joint_message_age_s': 0.1, 'servo_response_age_s': 0.2}
        snapshot = {'timestamp': 99.9, 'arm': {'mapping_confirmed': True, 'joints': {'joint1':joint}}}
        with patch.object(api.time, 'time', return_value=100.):
            path.write_text(json.dumps(snapshot))
            result = api.joint_compare(api.JointReference(joint='joint1', reference_rad=0.1))['arm']
            self.assertAlmostEqual(result['difference_rad'], 0.1)
            self.assertFalse(result['applied'])
            snapshot['arm']['joints']['joint1']['servo_response_age_s'] = 2
            path.write_text(json.dumps(snapshot))
            with self.assertRaises(HTTPException) as error:
                api.joint_compare(api.JointReference(joint='joint1', reference_rad=0.1))
            self.assertEqual(error.exception.detail, 'joint_unavailable')

    def test_rgb_depth_freezes_pair_and_checks_identity(self):
        import json
        path = self.root/'run/rgb-depth-pair.json'
        pair={'color_jpeg':'abc','depth_jpeg':'def','width':640,'height':360,'frame_id':'color',
              'color_stamp':99.,'depth_stamp':99.05,'created_at':99.}
        info={'width':640,'height':360,'matrix':[500,0,320,0,500,180,0,0,1],
              'distortion':[],'distortion_model':'plumb_bob','frame_id':'color','received_at':99.}
        (self.root/'run/ros-status.json').write_text(json.dumps({'timestamp':99.5,'camera_info':{'color':info,'depth':info}}))
        points=[api.AlignmentPoint(color_x=10,color_y=10,depth_x=13,depth_y=14)]*3
        with patch.object(api.time,'time',return_value=100.):
            path.write_text(json.dumps(pair))
            captured=api.rgb_depth_capture()
            result=api.rgb_depth_compare(api.AlignmentMeasurement(points=points,pair_id=captured['id']))['rgb_depth']
            self.assertTrue(result['image_pair_synchronized'])
            self.assertAlmostEqual(result['image_pair_time_difference_s'], .05)
            with self.assertRaises(HTTPException) as error:
                api.rgb_depth_compare(api.AlignmentMeasurement(points=points,pair_id='0'*32))
            self.assertEqual(error.exception.detail, 'rgb_depth_pair_expired')
            path.write_text(json.dumps(dict(pair,created_at=90.)))
            with self.assertRaises(HTTPException) as error: api.rgb_depth_capture()
            self.assertEqual(error.exception.detail,'rgb_depth_pair_unavailable')

    def test_rgb_depth_requires_live_matching_metadata_and_bounds(self):
        import json
        info = {'width':640,'height':360,'matrix':[500,0,320,0,500,180,0,0,1],
                'distortion':[],'distortion_model':'plumb_bob','frame_id':'color','received_at':98.}
        path = self.root / 'run/ros-status.json'
        points = [api.AlignmentPoint(color_x=10, color_y=10, depth_x=13, depth_y=14)] * 3
        with patch.object(api.time, 'time', return_value=100.):
            path.write_text(json.dumps({'timestamp':99.,'camera_info':{'color':info,'depth':info}}))
            result = api.rgb_depth_compare(api.AlignmentMeasurement(points=points))['rgb_depth']
            self.assertEqual(result['rms_px'], 5)
            self.assertFalse(result['image_pair_synchronized'])
            self.assertFalse(result['applied'])
            path.write_text(json.dumps({'timestamp':99.,'camera_info':{'color':info,'depth':dict(info,frame_id='other')}}))
            with self.assertRaises(HTTPException) as error: api.rgb_depth_compare(api.AlignmentMeasurement(points=points))
            self.assertEqual(error.exception.detail, 'camera_info_mismatch')
            path.write_text(json.dumps({'timestamp':90.,'camera_info':{'color':info,'depth':info}}))
            with self.assertRaises(HTTPException) as error: api.rgb_depth_compare(api.AlignmentMeasurement(points=points))
            self.assertEqual(error.exception.detail, 'camera_info_unavailable')
            path.write_text(json.dumps({'timestamp':99.,'camera_info':{'color':info,'depth':info}}))
            invalid = [api.AlignmentPoint(color_x=640, color_y=10, depth_x=0, depth_y=0)] * 3
            with self.assertRaises(HTTPException) as error: api.rgb_depth_compare(api.AlignmentMeasurement(points=invalid))
            self.assertEqual(error.exception.detail, 'alignment_out_of_bounds')

    def test_camera_info_freshness_and_validation(self):
        import json
        from types import SimpleNamespace
        from camera_info_status import camera_info_snapshot
        msg = SimpleNamespace(width=640, height=480, k=[500., 0., 320., 0., 501., 240., 0., 0., 1.],
                              d=[.1, .2], distortion_model='plumb_bob', header=SimpleNamespace(frame_id='camera_color'))
        info = camera_info_snapshot(msg, 98.)
        self.assertEqual(info['matrix'][0], 500.)
        path = self.root / 'run/ros-status.json'
        with patch.object(api.time, 'time', return_value=100.):
            path.write_text(json.dumps({'timestamp':99., 'camera_info':{'color':info}}))
            self.assertEqual(api.calibration_status()['camera_info']['color'], info)
            for snapshot in ({'timestamp':90., 'camera_info':{'color':info}},
                             {'timestamp':99., 'camera_info':{'color':dict(info, received_at=101.)}},
                             {'timestamp':99., 'camera_info':{'color':dict(info, matrix=[1])}}):
                path.write_text(json.dumps(snapshot))
                self.assertEqual(api.calibration_status()['camera_info'], {})
        msg.k[0] = float('nan')
        self.assertIsNone(camera_info_snapshot(msg, 99.))
        msg.k[0] = 0.
        self.assertIsNone(camera_info_snapshot(msg, 99.))

    def test_wheel_observations_are_manual_and_preserve_unknown(self):
        from pydantic import ValidationError
        data = api.WheelObservation(environment='simulation', front_left='forward', front_right='backward', rear_left='stopped', rear_right='unknown')
        result = api.wheel_observation(data)['wheel']
        self.assertEqual(result['wheels']['rear_right'], 'unknown')
        self.assertEqual(result['wheels']['front_right'], 'backward')
        self.assertFalse(result['speed_measured'])
        self.assertFalse(result['verified'])
        self.assertFalse(result['applied'])
        self.assertEqual(api.calibration_status()['history'][0]['kind'], 'wheel')
        with self.assertRaises(ValidationError):
            api.WheelObservation(environment='simulation', front_left='forward', front_right='invalid', rear_left='stopped', rear_right='unknown')
        api.state['running'] = 'imu'
        with self.assertRaises(HTTPException) as error:
            api.wheel_observation(data)
        self.assertEqual(error.exception.detail, 'busy')

    def test_odometry_comparison_signed_units_and_validation(self):
        from pydantic import ValidationError
        result = api.odometry_compare(api.OdometryComparison(motion='rotation', source='ekf', reference=-360, recorded=-350))['odometry']
        self.assertEqual((result['unit'], result['difference']), ('deg', 10))
        self.assertAlmostEqual(result['relative_error_percent'], 1000 / 360)
        self.assertFalse(result['applied'])
        self.assertEqual(api.calibration_status()['history'][0]['kind'], 'odometry')
        linear = api.odometry_compare(api.OdometryComparison(motion='lateral', source='encoder', reference=100, recorded=99))['odometry']
        self.assertEqual((linear['unit'], linear['difference'], linear['relative_error_percent']), ('cm', -1, -1))
        with self.assertRaises(HTTPException) as error:
            api.odometry_compare(api.OdometryComparison(motion='forward', source='encoder', reference=0, recorded=1))
        self.assertEqual(error.exception.detail, 'reference_too_small')
        for value in (float('nan'), 10001, True):
            with self.subTest(value=value), self.assertRaises(ValidationError):
                api.OdometryComparison(motion='forward', source='encoder', reference=value, recorded=1)
        with self.assertRaises(ValidationError):
            api.OdometryComparison(motion='forward', source='unknown', reference=1, recorded=1)

    def test_lidar_position_is_bounded_and_does_not_claim_orientation(self):
        from pydantic import ValidationError
        data = api.LidarPositionMeasurement(x_cm=9, y_cm=-2, z_cm=4)
        result = api.lidar_position_candidate(data)['lidar']
        self.assertEqual(result['translation_m'], [.09, -.02, .04])
        self.assertEqual((result['parent_frame'], result['child_frame']), ('base_link', 'lidar_link'))
        self.assertFalse(result['rotation_verified'])
        self.assertFalse(result['scan_frame_verified'])
        self.assertFalse(result['applied'])
        self.assertEqual(api.calibration_status()['history'][0]['kind'], 'lidar')
        for value in (float('nan'), 301, -301, True):
            with self.subTest(value=value), self.assertRaises(ValidationError):
                api.LidarPositionMeasurement(x_cm=value, y_cm=0, z_cm=0)
        api.state['running'] = 'imu'
        with self.assertRaises(HTTPException) as error:
            api.lidar_position_candidate(data)
        self.assertEqual(error.exception.detail, 'busy')

    def test_battery_multi_point_fit_and_duplicate_rejection(self):
        import json
        path=self.root/'run/ros-status.json'
        with patch.object(api.time,'time',return_value=100.):
            for sensor, stamp in [(10.,97.),(11.,98.),(12.,99.)]:
                path.write_text(json.dumps({'timestamp':99.9,'battery_received_at':stamp,'battery_voltage':sensor}))
                api.battery_sample(api.BatteryReference(reference_v=sensor+1))
            with self.assertRaises(HTTPException) as error:api.battery_sample(api.BatteryReference(reference_v=13.))
            self.assertEqual(error.exception.detail,'battery_duplicate_sample')
            result=api.battery_fit()['battery_fit']
            self.assertAlmostEqual(result['slope'],1.)
            self.assertAlmostEqual(result['intercept_v'],1.)
            self.assertAlmostEqual(result['rms_v'],0.)
            self.assertFalse(result['applied'])
            api.battery_samples_reset()
            self.assertEqual(api.calibration_status()['battery_samples'],[])
            self.assertIsNotNone(api.calibration_status()['battery_fit'])

    def test_battery_comparison_requires_fresh_valid_measurement(self):
        import json
        path = self.root / 'run/ros-status.json'
        snapshot = {'timestamp':99.0, 'battery_received_at':98.0, 'battery_voltage':12.4}
        path.write_text(json.dumps(snapshot))
        with patch.object(api.time, 'time', return_value=100.0):
            result = api.battery_compare(api.BatteryReference(reference_v=12.0))['battery']
            self.assertAlmostEqual(result['difference_v'], .4)
            self.assertAlmostEqual(result['relative_error_percent'], 100/30)
            self.assertFalse(result['applied'])
            for field, value in [('timestamp',90), ('battery_received_at',90), ('battery_voltage',float('nan')), ('battery_received_at',101)]:
                path.write_text(json.dumps(dict(snapshot, **{field:value})))
                with self.subTest(field=field), self.assertRaises(HTTPException) as error:
                    api.battery_compare(api.BatteryReference(reference_v=12.0))
                self.assertEqual(error.exception.detail, 'battery_unavailable')

    def test_failed_write_preserves_existing_candidates(self):
        before = api.save_result('imu', {'candidate': [1, 2, 3], 'applied': False})
        with patch.object(api.os, 'replace', side_effect=OSError('disk error')):
            with self.assertRaises(OSError):
                api.save_result('camera', {'applied': False})
        self.assertEqual(api.stored_results()['imu'], before)
        self.assertNotIn('camera', api.stored_results())

    def test_six_pose_workflow_saves_candidate_and_reset_keeps_it(self):
        import json
        from types import SimpleNamespace
        for axis, index in zip('xyz', range(3)):
            for suffix, sign in [('plus',1),('minus',-1)]:
                pose = axis + '_' + suffix
                vector = [0.0, 0.0, 0.0]
                vector[index] = sign * 9.80665
                data = {'pose':pose, 'mean':vector, 'frame_id':'imu_link', 'source_id':'same', 'samples':100, 'current_offset_m_s2':[0,0,0], 'current_scale':[1,1,1]}
                completed = SimpleNamespace(returncode=0, stdout=json.dumps({'result':data}))
                with patch.object(api.subprocess, 'run', return_value=completed):
                    api.state['running'] = 'accel_pose'
                    api.run_job('accel_pose', {'pose':pose})
                self.assertIsNone(api.state['error'])
        self.assertEqual(len(api.calibration_status()['accel_poses']), 6)
        self.assertFalse(api.calibration_status()['accel']['applied'])
        api.reset_accel()
        self.assertEqual(api.calibration_status()['accel_poses'], [])
        self.assertIsNotNone(api.calibration_status()['accel'])

    def test_busy_and_insufficient_images_are_rejected(self):
        with self.assertRaises(HTTPException) as error: api.camera_compute(api.Board(columns=7, rows=6, square_mm=25))
        self.assertEqual(error.exception.detail, 'image_count')
        api.state['running'] = 'imu'
        with self.assertRaises(HTTPException) as error: api.start_imu()
        self.assertEqual(error.exception.detail, 'busy')


class CalibrationAuthorizationTests(unittest.IsolatedAsyncioTestCase):
    async def test_viewer_read_and_operator_only_write(self):
        from starlette.responses import JSONResponse
        from test_access_control import request
        import access_control as auth
        async def allowed(req):
            return JSONResponse({'ok': True})
        with patch.dict(auth.sessions, {'viewer-token': ('viewer', time.monotonic() + 60),
                                       'operator-token': ('operator', time.monotonic() + 60)}, clear=True), \
             patch.dict('os.environ', {'JETINSPECT_LAN_IP': '', 'JETINSPECT_LAN_CIDR': ''}):
            viewer = 'jetinspect_session=viewer-token'
            operator = 'jetinspect_session=operator-token'
            self.assertEqual((await auth.access_guard(request('GET', '/api/calibration', cookie=viewer), allowed)).status_code, 200)
            self.assertEqual((await auth.access_guard(request('POST', '/api/calibration/imu', cookie=viewer), allowed)).status_code, 403)
            self.assertEqual((await auth.access_guard(request('POST', '/api/calibration/footprint', cookie=viewer), allowed)).status_code, 403)
            self.assertEqual((await auth.access_guard(request('POST', '/api/calibration/lidar-position', cookie=viewer), allowed)).status_code, 403)
            self.assertEqual((await auth.access_guard(request('POST', '/api/calibration/odometry-compare', cookie=viewer), allowed)).status_code, 403)
            self.assertEqual((await auth.access_guard(request('POST', '/api/calibration/wheel-observation', cookie=viewer), allowed)).status_code, 403)
            self.assertEqual((await auth.access_guard(request('POST', '/api/calibration/rgb-depth-compare', cookie=viewer), allowed)).status_code, 403)
            self.assertEqual((await auth.access_guard(request('POST', '/api/calibration/rgb-depth-capture', cookie=viewer), allowed)).status_code, 403)
            self.assertEqual((await auth.access_guard(request('POST', '/api/calibration/joint-compare', cookie=viewer), allowed)).status_code, 403)
            self.assertEqual((await auth.access_guard(request('POST', '/api/calibration/extrinsic-fit', cookie=viewer), allowed)).status_code, 403)
            self.assertEqual((await auth.access_guard(request('POST', '/api/calibration/hand-eye-fit', cookie=viewer), allowed)).status_code, 403)
            self.assertEqual((await auth.access_guard(request('POST', '/api/calibration/tcp-pivot-fit', cookie=viewer), allowed)).status_code, 403)
            self.assertEqual((await auth.access_guard(request('POST', '/api/calibration/gripper-width-sample', cookie=viewer), allowed)).status_code, 403)
            self.assertEqual((await auth.access_guard(request('POST', '/api/calibration/battery-fit', cookie=viewer), allowed)).status_code, 403)
            self.assertEqual((await auth.access_guard(request('POST', '/api/calibration/wheel-speed-compare', cookie=viewer), allowed)).status_code, 403)
            self.assertEqual((await auth.access_guard(request('POST', '/api/calibration/lidar-direction', cookie=viewer), allowed)).status_code, 403)
            self.assertEqual((await auth.access_guard(request('POST', '/api/calibration/odom-capture/start', cookie=viewer), allowed)).status_code, 403)
            self.assertEqual((await auth.access_guard(request('POST', '/api/calibration/history/' + 'a'*32 + '/restore-candidate', cookie=viewer), allowed)).status_code, 403)
            self.assertEqual((await auth.access_guard(request('POST', '/api/calibration/gyro-settings/apply', cookie=viewer), allowed)).status_code, 403)
            self.assertEqual((await auth.access_guard(request('POST', '/api/calibration/accel-settings/apply', cookie=viewer), allowed)).status_code, 403)
            self.assertEqual((await auth.access_guard(request('POST', '/api/calibration/accel-settings/restore', cookie=viewer), allowed)).status_code, 403)
            self.assertEqual((await auth.access_guard(request('POST', '/api/calibration/gyro-settings/restore', cookie=viewer), allowed)).status_code, 403)
            self.assertEqual((await auth.access_guard(request('POST', '/api/calibration/battery-compare', cookie=viewer), allowed)).status_code, 403)
            self.assertEqual((await auth.access_guard(request('POST', '/api/calibration/imu', cookie=operator), allowed)).status_code, 200)

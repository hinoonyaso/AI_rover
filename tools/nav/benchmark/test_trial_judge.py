import copy
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(__file__))
import trial_judge as j  # noqa: E402

GOAL = {'x': 1.05, 'y': 1.10, 'yaw_deg': 90.0}


def meta(**kw):
    m = {'scenario': 'A', 'goal': dict(GOAL), 'collision': None, 'outcome': None,
         'auto': {'action_status': 'succeeded', 'elapsed_s': 8.0, 'invalid_plan_cut_short': False,
                  'last_plan_end_to_goal_m': 0.03}}
    m.update(kw)
    return m


def scan(x=1.05, y=1.02, yaw=90.0, score=0.96, margin=0.15):
    return {'status': 'ok', 'x': x, 'y': y, 'yaw_deg': yaw, 'score': score, 'margin': margin,
            'trusted': j.scan_trusted(score, margin)}


class TrustRule(unittest.TestCase):
    def test_same_rule_as_scan_match_init(self):
        self.assertTrue(j.scan_trusted(0.80, 0.10))
        self.assertTrue(j.scan_trusted(0.95, 0.05))
        self.assertFalse(j.scan_trusted(0.861, 0.075))   # ab_mppi A01
        self.assertFalse(j.scan_trusted(0.944, 0.094))   # ab_mppi B01
        self.assertFalse(j.scan_trusted(0.79, 0.50))
        self.assertFalse(j.scan_trusted(0.99, 0.04))

    def test_parse_dry_run_log(self):
        log = ('[INFO] [scan_match_init]: #2 score=0.700  x=+0.696 y=+1.091 yaw=-93.5deg\n'
               '[INFO] [scan_match_init]: #1 score=0.914  x=+1.000 y=+0.120 yaw=+90.0deg\n')
        r = j.scan_result_from_text(log)
        self.assertEqual(r['status'], 'ok')
        self.assertEqual((r['x'], r['y'], r['yaw_deg']), (1.0, 0.12, 90.0))
        self.assertAlmostEqual(r['margin'], 0.214)
        self.assertTrue(r['trusted'])
        self.assertEqual(j.scan_result_from_text('no /map or /scan')['status'], 'no_candidates')


class Outcome(unittest.TestCase):
    def test_collision_none_is_not_success(self):
        m = j.apply_scan(meta(), scan())
        self.assertEqual(m['outcome'], 'pending_collision')
        m = j.set_collision(m, False, 'test')
        self.assertEqual(m['outcome'], 'success')

    def test_collision_true_fails_even_unmeasured(self):
        m = j.set_collision(meta(), True, 'test')
        self.assertEqual(m['outcome'], 'fail')

    def test_plan_cut_short_is_invalid_not_success(self):
        m = meta()
        m['auto']['invalid_plan_cut_short'] = True
        m = j.set_collision(j.apply_scan(m, scan()), False, 'test')
        self.assertEqual(m['outcome'], 'invalid')

    def test_nav_failure_and_measurement_failure_are_separate(self):
        m = meta()
        m['auto']['action_status'] = 'aborted'
        self.assertEqual(j.apply_scan(m, scan())['outcome'], 'abort')
        m2 = j.set_collision(j.apply_scan(meta(), {'status': 'timeout'}), False, 'test')
        self.assertEqual(m2['outcome'], 'unmeasured')
        self.assertIn('timeout', m2['outcome_reason'])

    def test_untrusted_scan_is_unmeasured_not_judged(self):
        m = j.set_collision(j.apply_scan(meta(), scan(score=0.861, margin=0.075)), False, 'test')
        self.assertEqual(m['outcome'], 'unmeasured')
        self.assertIsNone(m['measured_final'])

    def test_limits(self):
        far = j.set_collision(j.apply_scan(meta(), scan(y=0.94)), False, 'test')   # 16 cm short
        self.assertEqual(far['outcome'], 'fail')
        turned = j.set_collision(j.apply_scan(meta(), scan(yaw=115.0)), False, 'test')
        self.assertEqual(turned['outcome'], 'fail')
        b = meta(scenario='B')
        b['goal'] = {'x': 1.05, 'y': 1.40, 'yaw_deg': 90.0}
        off_line = j.set_collision(j.apply_scan(b, scan(x=1.171, y=1.341)), False, 'test')
        self.assertEqual(off_line['outcome'], 'fail')
        self.assertIn('line', off_line['outcome_reason'])
        slow = meta()
        slow['auto']['elapsed_s'] = 61.0
        self.assertEqual(j.set_collision(j.apply_scan(slow, scan()), False, 'test')['outcome'], 'fail')


class StopAndMvp(unittest.TestCase):
    def test_not_stopped_blocks_the_scan_judgement(self):
        m = meta()
        m['auto']['stopped_before_measure'] = False
        m = j.set_collision(j.apply_scan(m, {'status': 'not_stopped'}), False, 'test')
        self.assertEqual(m['outcome'], 'unmeasured')
        self.assertIn('not_stopped', m['outcome_reason'])
        self.assertFalse(m['mvp']['pass'])

    def test_mvp_is_separate_from_the_15cm_outcome(self):
        m = meta()
        m['auto']['stopped_before_measure'] = True
        m = j.set_collision(j.apply_scan(m, scan(y=0.97)), False, 'test')   # 13 cm short
        self.assertEqual(m['outcome'], 'success')            # test plan: <= 15 cm
        self.assertFalse(m['mvp']['pass'])                   # MVP: <= 10 cm
        m2 = j.set_collision(j.apply_scan(meta(), scan(y=1.03)), False, 'test')
        m2['auto']['stopped_before_measure'] = True
        self.assertTrue(j.rejudge(m2)['mvp']['pass'])

    def test_mvp_pending_until_everything_is_known(self):
        m = meta()
        m['auto']['stopped_before_measure'] = True
        m = j.apply_scan(m, scan(y=1.03))
        self.assertIsNone(m['mvp']['pass'])                  # collision unconfirmed
        legacy = j.set_collision(j.apply_scan(meta(), scan(y=1.03)), False, 'test')
        self.assertIsNone(legacy['mvp']['pass'])             # stop state unknown (old records)


class StopCheck(unittest.TestCase):
    def samples(self, t0, t1, v=0.0, w=0.0, hz=20):
        n = int((t1 - t0) * hz)
        return [(t0 + i / hz, v, w) for i in range(n + 1)]

    def test_fresh_and_still_is_stopped(self):
        ok, why = j.stop_state(self.samples(10.0, 12.0), now=12.0)
        self.assertTrue(ok)

    def test_silent_odom_is_never_stopped(self):
        ok, why = j.stop_state(self.samples(10.0, 12.0), now=13.0)   # last message 1 s ago
        self.assertFalse(ok)
        self.assertEqual(why, 'odom_stale')
        self.assertEqual(j.stop_state([], now=5.0), (False, 'no_odom'))

    def test_moving_or_too_short_is_not_stopped(self):
        moving = self.samples(10.0, 11.5) + self.samples(11.55, 12.0, v=0.05)
        self.assertEqual(j.stop_state(moving, now=12.0), (False, 'moving'))
        self.assertEqual(j.stop_state(self.samples(11.7, 12.0), now=12.0), (False, 'window_too_short'))
        self.assertEqual(j.stop_state(self.samples(10.0, 12.0, w=0.05), now=12.0)[1], 'moving')

    def test_safety_error_blocks_success_and_scan_judgement(self):
        m = meta()
        m['auto']['stopped_before_measure'] = True
        m['auto']['safety_error'] = 'goal cancel not acknowledged: cancel request not answered in 3 s'
        m = j.set_collision(j.apply_scan(m, scan()), False, 'test')
        self.assertEqual(m['outcome'], 'safety_error')
        self.assertIn('cancel', m['outcome_reason'])
        self.assertFalse(m['mvp']['pass'] is True)


class Preservation(unittest.TestCase):
    def test_failed_scan_keeps_previous_good_scan(self):
        m = j.apply_scan(meta(), scan(y=1.02))
        good = copy.deepcopy(m['scan_final'])
        for bad in ({'status': 'timeout'}, {'status': 'no_candidates'}, scan(score=0.85, margin=0.06)):
            m = j.apply_scan(m, bad)
            self.assertEqual(m['scan_final'], good)
            self.assertEqual(m['scan_attempt']['status'], bad['status'])

    def test_manual_pose_wins_and_is_not_overwritten(self):
        m = j.apply_manual(meta(), {'x': 1.03, 'y': 0.97, 'yaw_deg': 89.0})
        m = j.apply_scan(m, scan(y=1.02))
        self.assertEqual(m['measured_final']['source'], 'manual')
        self.assertEqual(m['scan_final']['y'], 1.02)  # scan still stored separately
        with self.assertRaises(ValueError):
            j.apply_manual(m, {'x': 0.0, 'y': 0.0, 'yaw_deg': 0.0})
        m = j.apply_manual(m, {'x': 1.05, 'y': 1.0, 'yaw_deg': 90.0}, overwrite=True)
        self.assertEqual(m['manual_final']['y'], 1.0)


class Legacy(unittest.TestCase):
    def test_tape_and_scan_records_split(self):
        old = meta()
        old['measured_final'] = {'x': 1.02, 'y': 0.97, 'yaw_deg': 88.1,
                                 'tape': {'forward_m': 0.855, 'left_m': -0.025, 'turn_deg': 0}}
        old['scan_measured_final'] = {'x': 1.046, 'y': 0.991, 'yaw_deg': 88.0, 'source': 'scan_match',
                                      'score': 0.861, 'margin': 0.075}
        old['collision'] = False
        old['outcome'] = 'success'
        m = j.migrate_legacy(old)
        self.assertEqual(m['manual_final']['x'], 1.02)
        self.assertFalse(m['scan_final']['trusted'])
        self.assertEqual(m['measured_final']['source'], 'manual')
        self.assertEqual(m['outcome_legacy'], 'success')
        self.assertNotIn('scan_measured_final', m)

    def test_scan_only_record_with_weak_margin_becomes_unmeasured(self):
        old = meta(scenario='B')
        old['goal'] = {'x': 1.05, 'y': 1.40, 'yaw_deg': 90.0}
        old['measured_final'] = {'x': 1.146, 'y': 1.341, 'yaw_deg': 94.5, 'source': 'scan_match',
                                 'score': 0.941, 'margin': 0.086}
        old['collision'] = False
        old['outcome'] = 'success'
        m = j.migrate_legacy(old)
        self.assertEqual(m['outcome'], 'unmeasured')
        self.assertEqual(m['outcome_legacy'], 'success')


class ConfirmLast(unittest.TestCase):
    def test_confirm_sets_none_once_and_reports_collisions(self):
        import json
        import tempfile
        import confirm_last_trial as c
        with tempfile.TemporaryDirectory() as d:
            mp, lp = os.path.join(d, 'meta.json'), os.path.join(d, 'last.json')
            m = meta()
            m['auto']['stopped_before_measure'] = True
            json.dump(j.apply_scan(m, scan(y=1.03)), open(mp, 'w'))
            json.dump({'meta': mp}, open(lp, 'w'))
            _, out = c.confirm(path_file=lp)
            self.assertIs(out['collision'], False)
            self.assertEqual(out['outcome'], 'success')
            _, again = c.confirm(path_file=lp)                # already confirmed: untouched
            self.assertEqual(again['collision_source'], out['collision_source'])
            _, hit = c.confirm(True, 'operator', path_file=lp)
            self.assertEqual(hit['outcome'], 'fail')
            self.assertEqual(c.confirm(path_file=os.path.join(d, 'missing.json')), (None, None))


if __name__ == '__main__':
    unittest.main()

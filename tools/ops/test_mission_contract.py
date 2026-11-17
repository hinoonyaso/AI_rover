"""Test mission contracts without ROS or hardware. / ROS와 하드웨어 없이 임무 계약을 시험한다."""
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).parent / 'backend'))
from mission_contract import ContractError, MissionState, TRANSITIONS, validate_create_request, validate_transition


class MissionContractTests(unittest.TestCase):
    def test_lifecycle_and_cancel_race(self):
        for start, end in [('created', 'queued'), ('queued', 'running'), ('running', 'cancel_requested'),
                           ('cancel_requested', 'canceled'), ('cancel_requested', 'succeeded'),
                           ('cancel_requested', 'failed'), ('running', 'interrupted')]:
            self.assertEqual(validate_transition(start, end), end)
        with self.assertRaises(ContractError):
            validate_transition('running', 'canceled')

    def test_terminal_states_are_immutable(self):
        for terminal in ('succeeded', 'failed', 'canceled', 'interrupted'):
            self.assertFalse(TRANSITIONS[MissionState(terminal)])
            for next_state in MissionState:
                with self.assertRaises(ContractError):
                    validate_transition(terminal, next_state)

    def test_reject_unknown_or_duplicate_transition(self):
        for current, target in [('created', 'created'), ('created', 'running'), ('invalid', 'running')]:
            with self.assertRaises(ContractError):
                validate_transition(current, target)

    def test_only_valid_mock_mission_is_accepted(self):
        request = {'request_id': '018f0000-0000-4000-8000-000000000001', 'mode': 'simulation', 'kind': 'inspection_demo', 'parameters': {}}
        self.assertEqual(validate_create_request(request), request)
        for field, value, code in [('mode', 'robot', 'mode_unavailable'), ('kind', 'inspect', 'unsupported_kind'),
                                   ('parameters', {'target': 'A'}, 'invalid_parameters'), ('request_id', 'bad', 'invalid_request_id')]:
            with self.subTest(field=field), self.assertRaises(ContractError) as err:
                validate_create_request({**request, field: value})
            self.assertEqual(err.exception.code, code)
        with self.assertRaises(ContractError):
            validate_create_request({**request, 'unexpected': True})


if __name__ == '__main__':
    unittest.main()

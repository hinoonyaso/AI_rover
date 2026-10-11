import os
import random
import sys
import unittest

sys.path.insert(0, os.path.dirname(__file__))
import grasp_contact as gc  # noqa: E402


class SimGripper:
    """Position follows the command with a 3-pulse dead band until it meets `block`; the jaws touch at 693."""

    def __init__(self, start=200, block=None, drop=0.0, seed=1):
        self.pos, self.block, self.drop = start, block, drop
        self.rng = random.Random(seed)
        self.moves = 0

    def move(self, pulse, ms):
        self.moves += 1
        stop = min(pulse, gc.CLOSED_END)
        if self.block is not None:
            stop = min(stop, self.block)
        if abs(stop - self.pos) > 3:
            self.pos = stop

    def read(self):
        return None if self.rng.random() < self.drop else self.pos


def run(g, **kw):
    return gc.find_contact(g.move, g.read, **kw)


WINDOW = (495, 555)


class Contact(unittest.TestCase):
    def test_cube_is_found_and_classified_as_object(self):
        for block in (519, 523, 527):
            g = SimGripper(block=block)
            r = run(g)
            self.assertEqual(r['status'], 'contact', block)
            self.assertAlmostEqual(r['contact'], block, delta=4)       # servo dead band 3-4 pulses
            self.assertEqual(gc.classify(r, WINDOW), 'object')

    def test_empty_close_is_never_a_contact(self):
        r = run(SimGripper(block=None))
        self.assertEqual(r['status'], 'no_contact')
        self.assertEqual(gc.classify(r, WINDOW), 'no_contact')

    def test_obstacle_outside_the_window_is_not_the_object(self):
        for block in (300, 440, 585, 640):          # fingers / a larger thing / something nearly closed
            r = run(SimGripper(block=block))
            self.assertEqual(r['status'], 'contact', block)
            self.assertEqual(gc.classify(r, WINDOW), 'outside_window', block)

    def test_missing_readings_never_produce_a_false_contact(self):
        outcomes = set()
        for seed in range(200):
            r = run(SimGripper(block=None, drop=0.3, seed=seed))
            outcomes.add(gc.classify(r, WINDOW))
            self.assertNotEqual(r['status'], 'contact', seed)   # nothing to touch: any 'contact' would be a false one
        self.assertTrue(outcomes <= {'no_contact', 'no_reading', 'bad_start'}, outcomes)   # all safe: no contact reported

    def test_cube_with_dropped_reads_is_found_or_aborted_never_misplaced(self):
        found = aborted = 0
        for seed in range(200):
            r = run(SimGripper(block=523, drop=0.3, seed=seed))
            if r['status'] == 'contact':
                found += 1
                self.assertAlmostEqual(r['contact'], 523, delta=5)     # never a wrong position
            else:
                aborted += 1
                self.assertIn(r['status'], ('no_reading', 'bad_start'))
        self.assertGreater(found, 0)
        self.assertEqual(found + aborted, 200)

    def test_persistent_silence_aborts(self):
        r = run(SimGripper(block=523, drop=1.0))
        self.assertEqual(r['status'], 'bad_start')               # no reading even at the start
        g = SimGripper(block=523)
        reads = iter([200, 212, None, None, None, None, None])
        r = gc.find_contact(g.move, lambda: next(reads, None))
        self.assertEqual(r['status'], 'no_reading')

    def test_nearly_closed_start_is_refused(self):
        self.assertEqual(run(SimGripper(start=500, block=600))['status'], 'bad_start')

    def test_step_is_limited_to_a_safe_range(self):
        g = SimGripper(block=523)
        run(g, step=100)                                          # asked for a huge step
        self.assertLess(g.moves, 40)                              # clamped to 16 -> about 20 steps, not 3
        self.assertEqual(run(SimGripper(block=523), step=100)['status'], 'contact')


if __name__ == '__main__':
    unittest.main()

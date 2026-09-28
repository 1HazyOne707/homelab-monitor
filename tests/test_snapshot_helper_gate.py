"""Exercises the missing-baseline gate in tests/snapshot_helper.py.

Verifies that assert_snapshot fails (instead of silently writing) when a
baseline file is missing, that UPDATE_SNAPSHOTS=1 still creates baselines
deliberately, and that match/mismatch comparison still works.
"""
import os
import unittest
from unittest.mock import patch

from tests.snapshot_helper import SNAP_DIR, assert_snapshot

GATE_TEST_NAME = "_gate_test_scratch_snapshot"


class SnapshotHelperGateTests(unittest.TestCase):
    def setUp(self):
        self.path = SNAP_DIR / f"{GATE_TEST_NAME}.json"
        # patch.dict via addCleanup restores the environment unconditionally —
        # even if a test or another cleanup raises. A leaked UPDATE_SNAPSHOTS=1
        # would make every later snapshot test self-baseline, which is exactly
        # the defect this file guards.
        env = patch.dict(os.environ)
        env.start()
        self.addCleanup(env.stop)
        os.environ.pop("UPDATE_SNAPSHOTS", None)
        self.addCleanup(self._unlink_scratch)
        # Make sure no stray file from a previous failed run is lying around.
        self._unlink_scratch()

    def _unlink_scratch(self):
        if self.path.exists():
            self.path.unlink()

    def test_missing_baseline_fails_and_creates_no_file(self):
        self.assertFalse(self.path.exists())
        with self.assertRaises(AssertionError):
            assert_snapshot(self, GATE_TEST_NAME, {"a": 1})
        self.assertFalse(
            self.path.exists(),
            "assert_snapshot must not write a baseline as a side effect of a failing call",
        )

    def test_update_snapshots_env_creates_missing_baseline(self):
        os.environ["UPDATE_SNAPSHOTS"] = "1"
        self.assertFalse(self.path.exists())
        assert_snapshot(self, GATE_TEST_NAME, {"a": 1})
        self.assertTrue(self.path.exists())

    def test_matching_existing_baseline_passes(self):
        os.environ["UPDATE_SNAPSHOTS"] = "1"
        assert_snapshot(self, GATE_TEST_NAME, {"a": 1})
        del os.environ["UPDATE_SNAPSHOTS"]
        # Should not raise.
        assert_snapshot(self, GATE_TEST_NAME, {"a": 1})

    def test_mismatching_existing_baseline_fails(self):
        os.environ["UPDATE_SNAPSHOTS"] = "1"
        assert_snapshot(self, GATE_TEST_NAME, {"a": 1})
        del os.environ["UPDATE_SNAPSHOTS"]
        with self.assertRaises(AssertionError):
            assert_snapshot(self, GATE_TEST_NAME, {"a": 2})


if __name__ == "__main__":
    unittest.main()

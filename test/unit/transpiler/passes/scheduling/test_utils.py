# This code is part of Qiskit.
#
# (C) Copyright IBM 2022.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""Tests for Qiskit scheduling utilities."""

from qiskit.test import QiskitTestCase

from qiskit_ibm_provider.transpiler.passes.scheduling.utils import (
    DynamicCircuitInstructionDurations,
)


class TestDynamicCircuitInstructionDurations(QiskitTestCase):
    """Tests the DynamicCircuitInstructionDurations patching"""

    def test_patch_measure(self):
        """Test if schedules circuits with c_if after measure with a common clbit.
        See: https://github.com/Qiskit/qiskit-terra/issues/7654"""

        durations = DynamicCircuitInstructionDurations(
            [
                ("x", None, 200),
                ("measure", None, 1000),
                ("measure", (0, 1), 1200),
                ("reset", None, 800),
            ]
        )

        self.assertEqual(durations.get("x", (0,)), 200)
        self.assertEqual(durations.get("measure", (0,)), 1160)
        self.assertEqual(durations.get("measure", (0, 1)), 1360)
        self.assertEqual(durations.get("reset", (0,)), 1160)

    def test_patch_disable(self):
        """Test if schedules circuits with c_if after measure with a common clbit.
        See: https://github.com/Qiskit/qiskit-terra/issues/7654"""

        durations = DynamicCircuitInstructionDurations(
            [("x", None, 200), ("measure", None, 1000), ("measure", (0, 1), 1200)],
            enable_patching=False,
        )

        self.assertEqual(durations.get("x", (0,)), 200)
        self.assertEqual(durations.get("measure", (0,)), 1000)
        self.assertEqual(durations.get("measure", (0, 1)), 1200)

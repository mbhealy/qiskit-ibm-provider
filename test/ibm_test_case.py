# This code is part of Qiskit.
#
# (C) Copyright IBM 2021.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""Custom TestCase for IBM Provider."""

import inspect
import logging
import os
import time
from typing import List, Any
from qiskit.test.base import BaseQiskitTestCase

from qiskit_ibm_provider import QISKIT_IBM_PROVIDER_LOGGER_NAME
from qiskit_ibm_provider.apiconstants import ApiJobStatus, API_JOB_FINAL_STATES
from qiskit_ibm_provider.job.exceptions import IBMJobNotFoundError
from .utils import setup_test_logging


class IBMTestCase(BaseQiskitTestCase):
    """Custom TestCase for use with qiskit-ibm-provider."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.log = logging.getLogger(cls.__name__)
        filename = "%s.log" % os.path.splitext(inspect.getfile(cls))[0]
        setup_test_logging(cls.log, filename)
        cls._set_logging_level(logging.getLogger(QISKIT_IBM_PROVIDER_LOGGER_NAME))

    @classmethod
    def simple_job_callback(cls, job_id, job_status, job, **kwargs):
        """A callback function that logs current job status."""
        # pylint: disable=unused-argument
        queue_info = kwargs.get("queue_info", "unknown")
        cls.log.info(
            "Job %s status is %s, queue_info is %s", job_id, job_status, queue_info
        )

    @classmethod
    def _set_logging_level(cls, logger: logging.Logger) -> None:
        """Set logging level for the input logger.

        Args:
            logger: Logger whose level is to be set.
        """
        if logger.level is logging.NOTSET:
            try:
                logger.setLevel(cls.log.level)
            except Exception as ex:  # pylint: disable=broad-except
                logger.warning(
                    'Error while trying to set the level for the "%s" logger to %s. %s.',
                    logger,
                    os.getenv("LOG_LEVEL"),
                    str(ex),
                )
        if not any(
            isinstance(handler, logging.StreamHandler) for handler in logger.handlers
        ):
            logger.addHandler(logging.StreamHandler())
            logger.propagate = False

    def setUp(self) -> None:
        """Test level setup."""
        super().setUp()
        # Record submitted jobs.
        self._jobs: List[Any] = []

    def tearDown(self) -> None:
        """Test level tear down."""
        super().tearDown()
        failed = False
        # It's surprisingly difficult to find out whether the test failed.
        # Using a private attribute is not ideal but it'll have to do.
        if self._outcome and self._outcome.errors:
            for _, exc_info in self._outcome.errors:
                if exc_info is not None:
                    failed = True

        if not failed:
            for client, job_id in self._jobs:
                try:
                    job_status = client.job_get(job_id)["status"]
                    if ApiJobStatus(job_status) not in API_JOB_FINAL_STATES:
                        client.job_cancel(job_id)
                        time.sleep(1)
                    retry = 3
                    while retry > 0:
                        try:
                            client.job_delete(job_id)
                            time.sleep(1)
                            retry -= 1
                        except IBMJobNotFoundError:
                            retry = 0
                except Exception:  # pylint: disable=broad-except
                    pass

#!/usr/bin/env python
"""
Use nosetests to run the unit tests for this project.

"""
import os
import sys
import logging

import nose

sys.path.insert(0, "./lib")

from director import utils
utils.log_init(logging.CRITICAL)

result = nose.core.TestProgram().success
nose.result.end_capture()


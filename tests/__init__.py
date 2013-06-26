# -*- coding: utf-8 -*-
"""
    __init__

    Test Suite

    :copyright: © 2013 by Openlabs Technologies & Consulting (P) Limited
    :license: AGPL with Openlabs Exception, see LICENSE for more details.
"""
import unittest
from .test_itsbroken import TestItsBroken


def suite():
    _suite = unittest.TestSuite()
    _suite.addTests([
        unittest.TestLoader().loadTestsFromTestCase(TestItsBroken),
    ])
    return _suite

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())

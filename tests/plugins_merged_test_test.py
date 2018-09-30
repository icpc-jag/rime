#!/usr/bin/python

import unittest

from rime.core import targets
from rime.plugins import merged_test


class MergedTestTest(unittest.TestCase):
    def testTestsetOverridden(self):
        self.assertTrue(targets.registry.Testset is merged_test.Testset)


if __name__ == '__main__':
    unittest.main()

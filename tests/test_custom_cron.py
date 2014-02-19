#! /usr/bin/python
# -*- encoding: utf8 -*-

import unittest

from src.custom_cron import CustomCron


class TestCustomCron(unittest.TestCase):

    def test_enough_args(self):
        args = ['NO_LOG', 'NO_MAIL', 'echo', 'hello', 'world']
        c = CustomCron(args)
        self.assertFalse(c.is_not_enough_args(), "Should be enough args")

    def test_not_enough_args(self):
        args = ['NO_LOG', 'NO_MAIL']
        c = CustomCron(args)
        self.assertTrue(c.is_not_enough_args(), "Should be not enough args")


if __name__ == "__main__":
    unittest.main()

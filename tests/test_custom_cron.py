#! /usr/bin/python
# -*- encoding: utf8 -*-

import os
import unittest

from src.custom_cron import CustomCron


class TestCustomCron(unittest.TestCase):

    def test_enough_args(self):
        args = ['NO_LOG', 'NO_MAIL', 'echo', 'hello', 'world']
        custom_cron = CustomCron(args)
        self.assertFalse(custom_cron.is_not_enough_args(), "Should be enough args")

    def test_not_enough_args(self):
        args = ['NO_LOG', 'NO_MAIL']
        custom_cron = CustomCron(args)
        self.assertTrue(custom_cron.is_not_enough_args(), "Should be not enough args")

    def test_parse_no_args(self):
        args = ['NO_LOG', 'NO_MAIL', 'echo', 'hello', 'world']
        custom_cron = CustomCron(args)
        custom_cron.parse_arguments()
        self.assertFalse(custom_cron.is_log_needed(), "Should not log")
        self.assertFalse(custom_cron.is_email_needed(), "Should not send mail")
        self.assertIsNone(custom_cron.log_path, "Should be None")
        self.assertIsNone(custom_cron.email_address, "Should be None")
        self.assertEqual(custom_cron.script_to_execute, "echo", "Bad command")
        self.assertEqual(len(custom_cron.script_to_execute_args), 2, "Unexpected number of parameters")
        self.assertEqual(custom_cron.script_to_execute_args[0], "hello", "Bad parameter")
        self.assertEqual(custom_cron.script_to_execute_args[1], "world", "Bad parameter")

    def test_parse_args(self):
        args = ['logfile.log', 'foo@bar.com', 'echo', 'hello']
        custom_cron = CustomCron(args)
        custom_cron.parse_arguments()
        self.assertTrue(custom_cron.is_log_needed(), "Should log")
        self.assertTrue(custom_cron.is_email_needed(), "Should send mail")
        self.assertEqual(custom_cron.log_path, "logfile.log", "Should be logfile.log")
        self.assertEqual(custom_cron.email_address, "foo@bar.com", "Should be foo@bar.com")
        self.assertEqual(custom_cron.script_to_execute, "echo", "Bad command")
        self.assertEqual(len(custom_cron.script_to_execute_args), 1, "Unexpected number of parameters")
        self.assertEqual(custom_cron.script_to_execute_args[0], "hello", "Bad parameter")

    def test_simple_hello_script(self):
        args = ['NO_LOG', 'NO_MAIL', './hello.sh']
        custom_cron = CustomCron(args)
        custom_cron.parse_arguments()
        custom_cron.execute_script()
        self.assertTrue(os.path.isfile("./world"), "Result file not found")
        with open("./world", 'r') as f:
            line = f.readline()
            self.assertEqual(line, "Hello World\n", "Content do not match")
        os.remove("./world")

    def test_args_hello_script(self):
        args = ['NO_LOG', 'NO_MAIL', './hello_args.sh', 'Hello', 'world', 'foo bar']
        custom_cron = CustomCron(args)
        custom_cron.parse_arguments()
        custom_cron.execute_script()
        self.assertTrue(os.path.isfile("./world_args"), "Result file not found")
        with open("./world_args", 'r') as f:
            line = f.readline()
            self.assertEqual(line, "Arg 1 : Hello - Arg 2 : world - Arg 3 : foo bar\n", "Content do not match")
        os.remove("./world_args")

    def test_log_hello_script(self):
        args = ['log', 'NO_MAIL', './hello.sh']
        custom_cron = CustomCron(args)
        custom_cron.parse_arguments()
        custom_cron.execute_script()
        custom_cron.write_log()
        self.assertTrue(os.path.isfile("./log"), "No log file created")
        with open("./log", 'r') as f:
            line = f.read()
            self.assertEqual(line, "So far so good !\n", "Content do not match")
        os.remove("./log")

    def test_log_hello_multiple_script(self):
        args = ['log', 'NO_MAIL', './hello.sh']
        custom_cron = CustomCron(args)
        custom_cron.parse_arguments()
        custom_cron.execute_script()
        custom_cron.write_log()
        custom_cron.write_log()
        self.assertTrue(os.path.isfile("./log"), "No log file created")
        with open("./log", 'r') as f:
            line = f.read()
            self.assertEqual(line, "So far so good !\nSo far so good !\n", "Content do not match")
        os.remove("./log")

    def test_log_error_script(self):
        args = ['log', 'NO_MAIL', './error.sh']
        custom_cron = CustomCron(args)
        custom_cron.parse_arguments()
        custom_cron.execute_script()
        custom_cron.write_log()
        self.assertTrue(os.path.isfile("./log"), "No log file created")
        with open("./log", 'r') as f:
            line = f.read()
            self.assertEqual(line, "So far so good !\ncp: missing file operand\nTry 'cp --help' for more information.\n", "Content do not match")
        os.remove("./log")

if __name__ == "__main__":
    unittest.main()

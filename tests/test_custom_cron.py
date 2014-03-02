#! /usr/bin/python
# -*- encoding: utf8 -*-

import asyncore
import os
import smtpd
import smtplib
import unittest
import threading

from src.custom_cron import CustomCron


class TestCustomCron(unittest.TestCase):

    def setUp(self):
        unittest.TestCase.setUp(self)
        self.server_thread = None

    def tearDown(self):
        unittest.TestCase.tearDown(self)
        if self.server_thread is not None:
            self.server_thread.stop()

    def test_enough_args(self):
        args = ['custom_cron.py', 'NO_LOG', 'NO_MAIL', 'echo', 'hello', 'world']
        custom_cron = CustomCron(args)
        self.assertFalse(custom_cron.is_not_enough_args(), "Should be enough args")

    def test_not_enough_args(self):
        args = ['custom_cron.py', 'NO_LOG', 'NO_MAIL']
        custom_cron = CustomCron(args)
        self.assertTrue(custom_cron.is_not_enough_args(), "Should be not enough args")

    def test_parse_no_args(self):
        args = ['custom_cron.py', 'NO_LOG', 'NO_MAIL', 'echo', 'hello', 'world']
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
        args = ['custom_cron.py', 'logfile.log', 'foo@bar.com', 'echo', 'hello']
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
        args = ['custom_cron.py', 'NO_LOG', 'NO_MAIL', './hello.sh']
        custom_cron = CustomCron(args)
        custom_cron.parse_arguments()
        custom_cron.execute_script()
        self.assertTrue(os.path.isfile("./world"), "Result file not found")
        with open("./world", 'r') as f:
            line = f.readline()
            self.assertEqual(line, "Hello World\n", "Content do not match")
        os.remove("./world")

    def test_args_hello_script(self):
        args = ['custom_cron.py', 'NO_LOG', 'NO_MAIL', './hello_args.sh', 'Hello', 'world', 'foo bar']
        custom_cron = CustomCron(args)
        custom_cron.parse_arguments()
        custom_cron.execute_script()
        self.assertTrue(os.path.isfile("./world_args"), "Result file not found")
        with open("./world_args", 'r') as f:
            line = f.readline()
            self.assertEqual(line, "Arg 1 : Hello - Arg 2 : world - Arg 3 : foo bar\n", "Content do not match")
        os.remove("./world_args")

    def test_log_script_not_found(self):
        args = ['custom_cron.py', 'log', 'NO_MAIL', './unknow.sh']
        custom_cron = CustomCron(args)
        custom_cron.parse_arguments()
        custom_cron.execute_script()
        custom_cron.write_log()
        self.assertTrue(os.path.isfile("./log"), "No log file created")
        with open("./log", 'r') as f:
            line = f.read()
            self.assertEqual(line, "ERROR : Script ./unknow.sh not found\n", "Content do not match")
        os.remove("./log")

    def test_log_hello_script(self):
        args = ['custom_cron.py', 'log', 'NO_MAIL', './hello.sh']
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
        args = ['custom_cron.py', 'log', 'NO_MAIL', './hello.sh']
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
        args = ['custom_cron.py', 'log', 'NO_MAIL', './error.sh']
        custom_cron = CustomCron(args)
        custom_cron.parse_arguments()
        custom_cron.execute_script()
        custom_cron.write_log()
        self.assertTrue(os.path.isfile("./log"), "No log file created")
        with open("./log", 'r') as f:
            line = f.read()
            self.assertEqual(line, "So far so good !\ncp: missing file operand\nTry 'cp --help' for more information.\n", "Content do not match")
        os.remove("./log")

    def test_mail_hello_script(self):
        self.server_thread = self._instanciate_local_smtp_server(1025)
        local_smtp_server = self.server_thread.server
        smtp_connection = smtplib.SMTP('127.0.0.1', 1025)
        args = ['custom_cron.py', 'NO_LOG', 'test@localhost', './hello.sh']
        custom_cron = CustomCron(args)
        custom_cron.parse_arguments()
        custom_cron.execute_script()
        custom_cron.send_email(smtp_connection)
        self.assertEqual(len(local_smtp_server.rcpttos), 1)
        self.assertEqual(local_smtp_server.rcpttos[0], 'test@localhost', 'Wrong dest email')
        self.assertEqual(local_smtp_server.data, 'Content-Type: text/plain; charset="us-ascii"\nMIME-Version: 1.0\nContent-Transfer-Encoding: 7bit\nSubject: [Cron : OK] <' + os.uname()[1] + '> : ./hello.sh\nFrom: custom_cron\nTo: test@localhost\n\nSo far so good !', 'Bad message')

    def test_mail_error_script(self):
        self.server_thread = self._instanciate_local_smtp_server(1026)
        local_smtp_server = self.server_thread.server
        smtp_connection = smtplib.SMTP('127.0.0.1', 1026)
        args = ['custom_cron.py', 'NO_LOG', 'test@localhost', './error.sh']
        custom_cron = CustomCron(args)
        custom_cron.parse_arguments()
        custom_cron.execute_script()
        custom_cron.send_email(smtp_connection)
        self.assertEqual(len(local_smtp_server.rcpttos), 1)
        self.assertEqual(local_smtp_server.rcpttos[0], 'test@localhost', 'Wrong dest email')
        mail_content = 'Content-Type: text/plain; charset="us-ascii"\nMIME-Version: 1.0\nContent-Transfer-Encoding: 7bit\nSubject: [Cron : FAIL] <' + os.uname()[1] + '> : ./error.sh\nFrom: custom_cron\nTo: test@localhost\n\nSo far so good !\ncp: missing file operand\nTry \'cp --help\' for more information.' 
        self.assertEqual(local_smtp_server.data, mail_content, 'Bad message')

    def test_multiple_mails_hello_script(self):
        self.server_thread = self._instanciate_local_smtp_server(1027)
        local_smtp_server = self.server_thread.server
        smtp_connection = smtplib.SMTP('127.0.0.1', 1027)
        args = ['custom_cron.py', 'NO_LOG', 'test@localhost,foo@bar', './hello.sh']
        custom_cron = CustomCron(args)
        custom_cron.parse_arguments()
        custom_cron.execute_script()
        custom_cron.send_email(smtp_connection)
        self.assertEqual(len(local_smtp_server.rcpttos), 2)
        self.assertEqual(local_smtp_server.rcpttos[0], 'test@localhost', 'Wrong dest email')
        self.assertEqual(local_smtp_server.rcpttos[1], 'foo@bar', 'Wrong dest email')
        self.assertEqual(local_smtp_server.data, 'Content-Type: text/plain; charset="us-ascii"\nMIME-Version: 1.0\nContent-Transfer-Encoding: 7bit\nSubject: [Cron : OK] <' + os.uname()[1] + '> : ./hello.sh\nFrom: custom_cron\nTo: test@localhost,foo@bar\n\nSo far so good !', 'Bad message')

    def _instanciate_local_smtp_server(self, port):
        smtp_server = LocalSMTPServer(port)
        smtp_server.start()
        while smtp_server.ready is not True:
            pass
        return smtp_server


class LocalSMTPServer(threading.Thread):

    def __init__(self, port):
        threading.Thread.__init__(self)
        self.ready = False
        self.server = None
        self._port = port

    def run(self):
        self.server = CustomSMTPServer(('127.0.0.1', self._port), None)
        self.ready = True
        asyncore.loop(timeout=1)

    def stop(self):
        self.server.close()


class CustomSMTPServer(smtpd.SMTPServer):

    def __init__(self, local_addr, remote_addr):
        smtpd.SMTPServer.__init__(self, local_addr, remote_addr)
        self.peer = None
        self.mailfrom = None
        self.rcpttos = None
        self.data = None

    def process_message(self, peer, mailfrom, rcpttos, data):
        self.peer = peer
        self.mailfrom = mailfrom
        self.rcpttos = rcpttos
        self.data = data
        return

if __name__ == "__main__":
    unittest.main()

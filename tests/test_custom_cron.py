#! /usr/bin/python3
# -*- encoding: utf8 -*-

import asyncore
import os
import smtpd
import unittest
import threading

from src.custom_cron import CustomCron


class TestCustomCron(unittest.TestCase):

    def setUp(self):
        unittest.TestCase.setUp(self)
        self.server_thread = None
        self.args = ScriptArguments()

    def tearDown(self):
        unittest.TestCase.tearDown(self)
        if self.server_thread is not None:
            self.server_thread.stop()
        if os.path.isfile("/tmp/log"):
            os.remove("/tmp/log")

    def test_simple_hello_script(self):
        self.args.script_to_execute = './hello.sh'
        custom_cron = CustomCron(self.args)
        custom_cron.execute_script()
        self.assertTrue(os.path.isfile("./world"), "Result file not found")
        with open("./world", 'r') as f:
            line = f.readline()
        os.remove("./world")
        self.assertEqual(line, "Hello World\n", "Content do not match")

    def test_args_hello_script(self):
        self.args.script_to_execute = './hello_args.sh'
        self.args.script_to_execute_args = ['Hello', 'world', 'foo bar']
        custom_cron = CustomCron(self.args)
        custom_cron.execute_script()
        self.assertTrue(os.path.isfile("./world_args"), "Result file not found")
        with open("./world_args", 'r') as f:
            line = f.readline()
        os.remove("./world_args")
        self.assertEqual(line, "Arg 1 : Hello - Arg 2 : world - Arg 3 : foo bar\n", "Content do not match")

    def test_log_script_not_found(self):
        self.args.script_to_execute = './unknown.sh'
        self.args.log_path = '/tmp/log'
        custom_cron = CustomCron(self.args)
        custom_cron.execute_script()
        self.assertTrue(os.path.isfile("/tmp/log"), "No log file created")
        with open("/tmp/log", 'r') as f:
            line = f.read()
        self.assertEqual(line, "ERROR : Script ./unknown.sh not found\n", "Content do not match")

    def test_log_hello_script(self):
        self.args.script_to_execute = './hello.sh'
        self.args.log_path = '/tmp/log'
        custom_cron = CustomCron(self.args)
        custom_cron.execute_script()
        self.assertTrue(os.path.isfile("/tmp/log"), "No log file created")
        with open("/tmp/log", 'r') as f:
            line = f.read()
        self.assertEqual(line, "So far so good !\n", "Content do not match")

    def test_log_error_script(self):
        self.args.script_to_execute = './error.sh'
        self.args.log_path = '/tmp/log'
        custom_cron = CustomCron(self.args)
        custom_cron.execute_script()
        self.assertTrue(os.path.isfile("/tmp/log"), "No log file created")
        with open("/tmp/log", 'r') as f:
            line = f.read()
        self.assertEqual(line, "So far so good !\ncp: missing file operand\nTry 'cp --help' for more information.\n", "Content do not match")

    def test_mail_hello_script(self):
        self.server_thread = self._instanciate_local_smtp_server(1025)
        local_smtp_server = self.server_thread.server
        self.args.smtp_host = '127.0.0.1'
        self.args.smtp_port = 1025
        self.args.script_to_execute = './hello.sh'
        self.args.email_address = 'test@localhost'
        custom_cron = CustomCron(self.args)
        custom_cron.execute_script()
        self.assertEqual(len(local_smtp_server.rcpttos), 1)
        self.assertEqual(local_smtp_server.rcpttos[0], 'test@localhost', 'Wrong dest email')
        self.assertEqual(local_smtp_server.data, 'Content-Type: text/plain; charset="us-ascii"\nMIME-Version: 1.0\nContent-Transfer-Encoding: 7bit\nSubject: [Cron : OK] <' + os.uname()[1] + '> : ./hello.sh\nFrom: custom_cron\nTo: test@localhost\n\nSo far so good !', 'Bad message')

    def test_mail_error_script(self):
        self.server_thread = self._instanciate_local_smtp_server(1026)
        local_smtp_server = self.server_thread.server
        self.args.smtp_host = '127.0.0.1'
        self.args.smtp_port = 1026
        self.args.script_to_execute = './error.sh'
        self.args.email_address = 'test@localhost'
        custom_cron = CustomCron(self.args)
        custom_cron.execute_script()
        self.assertEqual(len(local_smtp_server.rcpttos), 1)
        self.assertEqual(local_smtp_server.rcpttos[0], 'test@localhost', 'Wrong dest email')
        mail_content = 'Content-Type: text/plain; charset="us-ascii"\nMIME-Version: 1.0\nContent-Transfer-Encoding: 7bit\nSubject: [Cron : FAIL] <' + os.uname()[1] + '> : ./error.sh\nFrom: custom_cron\nTo: test@localhost\n\nSo far so good !\ncp: missing file operand\nTry \'cp --help\' for more information.'
        self.assertEqual(local_smtp_server.data, mail_content, 'Bad message')

    def test_multiple_mails_hello_script(self):
        self.server_thread = self._instanciate_local_smtp_server(1027)
        local_smtp_server = self.server_thread.server
        self.args.smtp_host = '127.0.0.1'
        self.args.smtp_port = 1027
        self.args.script_to_execute = './hello.sh'
        self.args.email_address = 'test@localhost,foo@bar'
        custom_cron = CustomCron(self.args)
        custom_cron.execute_script()
        self.assertEqual(len(local_smtp_server.rcpttos), 2)
        self.assertEqual(local_smtp_server.rcpttos[0], 'test@localhost', 'Wrong dest email')
        self.assertEqual(local_smtp_server.rcpttos[1], 'foo@bar', 'Wrong dest email')
        self.assertEqual(local_smtp_server.data, 'Content-Type: text/plain; charset="us-ascii"\nMIME-Version: 1.0\nContent-Transfer-Encoding: 7bit\nSubject: [Cron : OK] <' + os.uname()[1] + '> : ./hello.sh\nFrom: custom_cron\nTo: test@localhost,foo@bar\n\nSo far so good !', 'Bad message')

    def test_subjet_mail_script_not_exists(self):
        self.server_thread = self._instanciate_local_smtp_server(1028)
        local_smtp_server = self.server_thread.server
        self.args.smtp_host = '127.0.0.1'
        self.args.smtp_port = 1028
        self.args.script_to_execute = './unknown.sh'
        self.args.email_address = 'test@localhost'
        custom_cron = CustomCron(self.args)
        custom_cron.execute_script()
        self.assertEqual(len(local_smtp_server.rcpttos), 1)
        self.assertEqual(local_smtp_server.rcpttos[0], 'test@localhost', 'Wrong dest email')
        self.assertEqual(local_smtp_server.data, 'Content-Type: text/plain; charset="us-ascii"\nMIME-Version: 1.0\nContent-Transfer-Encoding: 7bit\nSubject: [Cron : FAIL] <' + os.uname()[1] + '> : ./unknown.sh\nFrom: custom_cron\nTo: test@localhost\n\nERROR : Script ./unknown.sh not found', 'Bad message')

    def test_email_if_option_and_status_ko(self):
        self.server_thread = self._instanciate_local_smtp_server(1029)
        local_smtp_server = self.server_thread.server
        self.args.smtp_host = '127.0.0.1'
        self.args.smtp_port = 1029
        self.args.script_to_execute = './unknown.sh'
        self.args.email_address = 'test@localhost'
        self.args.email_only_on_fail = True
        custom_cron = CustomCron(self.args)
        custom_cron.execute_script()
        self.assertEqual(len(local_smtp_server.rcpttos), 1)
        self.assertEqual(local_smtp_server.rcpttos[0], 'test@localhost', 'Wrong dest email')
        self.assertEqual(local_smtp_server.data, 'Content-Type: text/plain; charset="us-ascii"\nMIME-Version: 1.0\nContent-Transfer-Encoding: 7bit\nSubject: [Cron : FAIL] <' + os.uname()[1] + '> : ./unknown.sh\nFrom: custom_cron\nTo: test@localhost\n\nERROR : Script ./unknown.sh not found', 'Bad message')

    def test_no_email_if_option_and_status_ok(self):
        self.server_thread = self._instanciate_local_smtp_server(1030)
        local_smtp_server = self.server_thread.server
        self.args.smtp_host = '127.0.0.1'
        self.args.smtp_port = 1030
        self.args.script_to_execute = './hello.sh'
        self.args.email_address = 'test@localhost'
        self.args.email_only_on_fail = True
        custom_cron = CustomCron(self.args)
        custom_cron.execute_script()
        self.assertIsNone(local_smtp_server.rcpttos, 'Should not receive email')

    def test_configuration_file_default_path(self):
        self.server_thread = self._instanciate_local_smtp_server(1031)
        local_smtp_server = self.server_thread.server
        self.args.smtp_host = '127.0.0.1'
        self.args.smtp_port = 1031
        self.args.configuration_path = os.getcwd() + '/configuration.ini'
        custom_cron = CustomCron(self.args)
        custom_cron.execute_script()
        self.assertTrue(os.path.isfile("/tmp/log"), "Result file not found")
        with open("/tmp/log", 'r') as f:
            line = f.readline()
        if os.path.isfile("./world_args"):
            os.remove("./world_args")
        self.assertEqual(line, "Arg 1 : Hello - Arg 2 : world - Arg 3 : bar\n", "Content do not match")
        self.assertEqual(len(local_smtp_server.rcpttos), 2)
        self.assertEqual(local_smtp_server.rcpttos[0], 'test@localhost', 'Wrong dest email')
        self.assertEqual(local_smtp_server.rcpttos[1], 'foo@bar', 'Wrong dest email')
        self.assertEqual(local_smtp_server.data, 'Content-Type: text/plain; charset="us-ascii"\nMIME-Version: 1.0\nContent-Transfer-Encoding: 7bit\nSubject: [Cron : OK] <' + os.uname()[1] + '> : ./hello_args.sh\nFrom: custom_cron\nTo: test@localhost,foo@bar\n\nArg 1 : Hello - Arg 2 : world - Arg 3 : bar', 'Bad message')

    def test_configuration_file_but_arg_precedence(self):
        self.server_thread = self._instanciate_local_smtp_server(1032)
        local_smtp_server = self.server_thread.server
        self.args.smtp_host = '127.0.0.1'
        self.args.smtp_port = 1032
        self.args.configuration_path = os.getcwd() + '/configuration.ini'
        self.args.log_path = '/tmp/log2'
        self.args.email_address = 'admin@company.com'
        self.args.email_only_on_fail = True
        self.args.script_to_execute = './error.sh'
        custom_cron = CustomCron(self.args)
        custom_cron.execute_script()
        self.assertTrue(os.path.isfile("/tmp/log2"), "Result file not found")
        with open("/tmp/log2", 'r') as f:
            line = f.read()
        os.remove("/tmp/log2")
        self.assertEqual(line, "So far so good !\ncp: missing file operand\nTry 'cp --help' for more information.\n", "Content do not match")
        self.assertEqual(len(local_smtp_server.rcpttos), 1)
        self.assertEqual(local_smtp_server.rcpttos[0], 'admin@company.com', 'Wrong dest email')
        self.assertEqual(local_smtp_server.data, 'Content-Type: text/plain; charset="us-ascii"\nMIME-Version: 1.0\nContent-Transfer-Encoding: 7bit\nSubject: [Cron : FAIL] <' + os.uname()[1] + '> : ./error.sh\nFrom: custom_cron\nTo: admin@company.com\n\nSo far so good !\ncp: missing file operand\nTry \'cp --help\' for more information.', 'Bad message')

    def test_minimalist_configuration_file(self):
        self.args.configuration_path = os.getcwd() + '/minimalist_configuration.ini'
        custom_cron = CustomCron(self.args)
        custom_cron.execute_script()
        with open("./world_args", 'r') as f:
            line = f.readline()
        os.remove("./world_args")
        self.assertEqual(line, "Arg 1 :  - Arg 2 :  - Arg 3 : \n", "Content do not match")

    def test_no_script_given(self):
        self.args.configuration_path = os.getcwd() + '/empty_configuration.ini'
        self.args.log_path = '/tmp/log'
        custom_cron = CustomCron(self.args)
        custom_cron.execute_script()
        self.assertTrue(os.path.isfile("/tmp/log"), "No log file created")
        with open("/tmp/log", 'r') as f:
            line = f.read()
        self.assertEqual(line, "ERROR : No script given\n", "Content do not match")

    def test_configure_smtp_with_cli(self):
        self.server_thread = self._instanciate_local_smtp_server(1033)
        local_smtp_server = self.server_thread.server
        self.args.script_to_execute = './hello.sh'
        self.args.email_address = 'test@localhost'
        self.args.smtp_host = '127.0.0.1'
        self.args.smtp_port = 1033
        custom_cron = CustomCron(self.args)
        custom_cron.execute_script()
        self.assertEqual(len(local_smtp_server.rcpttos), 1)
        self.assertEqual(local_smtp_server.rcpttos[0], 'test@localhost', 'Wrong dest email')
        self.assertEqual(local_smtp_server.data, 'Content-Type: text/plain; charset="us-ascii"\nMIME-Version: 1.0\nContent-Transfer-Encoding: 7bit\nSubject: [Cron : OK] <' + os.uname()[1] + '> : ./hello.sh\nFrom: custom_cron\nTo: test@localhost\n\nSo far so good !', 'Bad message')

    def _instanciate_local_smtp_server(self, port):
        smtp_server = LocalSMTPServer(port)
        smtp_server.start()
        while smtp_server.ready is not True:
            pass
        return smtp_server


class ScriptArguments(object):

    def __init__(self):
        self.log_path = None
        self.configuration_path = None
        self.smtp_host = None
        self.smtp_port = None
        self.smtp_login = None
        self.smtp_password = None
        self.email_address = None
        self.email_only_on_fail = False
        self.script_to_execute = None
        self.script_to_execute_args = []


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
        smtpd.SMTPServer.__init__(self, local_addr, remote_addr, decode_data=True)
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

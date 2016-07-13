#! /usr/bin/python3
# -*- encoding: utf8 -*-

import subprocess, os, sys
from smtplib import SMTP, SMTPNotSupportedError
from tempfile import TemporaryFile
from email.mime.text import MIMEText
import argparse
import configparser


class CustomCron(object):

    def __init__(self, args):
        self.configuration_path = None
        self.log_path = None
        self.email_address = None
        self.email_only_on_fail = False
        self.smtp_connection = {
            'host': None,
            'port': None,
            'login': None,
            'password': None
        }
        self.script_to_execute = None
        self.script_to_execute_args = []
        self._initialize_configuration(args)

    def execute_script(self):
        script_exit_code, script_output = self._execute_script()
        print(script_output)
        if self._is_log_needed():
            self._write_log(script_output)
        if self._is_email_needed():
            self._send_email(script_exit_code, script_output)

    def _initialize_configuration(self, args):
        self.configuration_path = args.configuration_path
        if self.configuration_path is not None:
            self._load_configuration_file()
        if args.log_path is not None:
            self.log_path = args.log_path
        if args.smtp_host is not None:
            self.smtp_connection = {
                'host': args.smtp_host,
                'port': args.smtp_port,
                'login': args.smtp_login,
                'password': args.smtp_password
            }
        if args.email_address is not None:
            self.email_address = args.email_address
        if self.email_only_on_fail != args.email_only_on_fail:
            self.email_only_on_fail = args.email_only_on_fail
        if args.script_to_execute is not None:
            self.script_to_execute = args.script_to_execute
        if len(args.script_to_execute_args) > 0:
            self.script_to_execute_args = args.script_to_execute_args

    def _load_configuration_file(self):
        if self.configuration_path is None or not os.path.isfile(self.configuration_path):
            return
        config = configparser.ConfigParser()
        config.read(self.configuration_path)
        if "log" in config:
            self.log_path = config["log"]["path"] if "path" in config["log"] else None
        if "email" in config:
            self.email_address = config["email"]["to"] if "to" in config["email"] else None
            self.email_only_on_fail = config["email"].getboolean("only_on_fail") if "only_on_fail" in config["email"] else False
        if "script" in config:
            self.script_to_execute = config["script"]["path"] if "path" in config["script"] else None
            self.script_to_execute_args = config["script"]["arguments"].split(' ') if "arguments" in config["script"] else []

    def _execute_script(self):
        if self.script_to_execute is None:
            script_output = "ERROR : No script given\n".format(self.script_to_execute)
            return 1, script_output
        if not os.path.isfile(self.script_to_execute):
            script_output = "ERROR : Script {0} not found\n".format(self.script_to_execute)
            return 1, script_output
        script_args = [self.script_to_execute] + self.script_to_execute_args
        with TemporaryFile(mode='w+t', encoding='utf-8') as tmp_log:
            script_exit_code = subprocess.call(script_args, stdout=tmp_log, stderr=subprocess.STDOUT)
            tmp_log.seek(0)
            script_output = tmp_log.read()
        return script_exit_code, script_output

    def _is_log_needed(self):
        return self.log_path is not None

    def _is_email_needed(self):
        return self.email_address is not None

    def _write_log(self, script_output):
        with open(self.log_path, 'a', encoding='utf-8') as log:
            log.write(script_output)

    def _send_email(self, script_exit_code, script_output):
        if self.email_only_on_fail and script_exit_code == 0:
            return
        subject = "[Cron : OK]" if script_exit_code == 0 else "[Cron : FAIL]"
        msg = MIMEText(script_output)
        hostname = os.uname()[1]
        msg['Subject'] = "{0} <{1}> : {2}".format(subject, hostname, self.script_to_execute)
        msg['From'] = 'custom_cron'
        msg['To'] = self.email_address
        smtp_connection = self._connect_to_smtp()
        smtp_connection.sendmail('custom_cron', self.email_address.split(','), msg.as_string())
        smtp_connection.quit()

    def _connect_to_smtp(self):
        smtp_ten_minutes_timeout = 10*60
        smtp_connection = SMTP(self.smtp_connection['host'], self.smtp_connection['port'], smtp_ten_minutes_timeout)
        smtp_connection.ehlo()
        try:
            smtp_connection.starttls()
            smtp_connection.ehlo()
        except SMTPNotSupportedError:
            # STARTTLS is not supported by the SMTP server, continue
            pass
        if self.smtp_connection['login'] is not None or self.smtp_connection['password'] is not None:
            smtp_connection.login(self.smtp_connection['login'], self.smtp_connection['password'])
        return smtp_connection


class ArgumentsParser(object):

    def __init__(self):
        self.parser = argparse.ArgumentParser(
            description='Handle the execution of an other script in order to log and/or send the result by email')
        self.parser.add_argument('--configuration',
                                 action='store',
                                 default=None,
                                 dest='configuration_path',
                                 help='path to the configuration file')
        self.parser.add_argument('--logfile',
                                 action='store',
                                 default=None,
                                 dest='log_path',
                                 help='path where to log the output')
        self.parser.add_argument('--smtp_host',
                                 action='store',
                                 default=None,
                                 dest='smtp_host',
                                 help='URL or IP address of the SMTP server')
        self.parser.add_argument('--smtp_port',
                                 action='store',
                                 default=25,
                                 dest='smtp_port',
                                 help='port of the SMTP server (default: 25)')
        self.parser.add_argument('--smtp_login',
                                 action='store',
                                 default=None,
                                 dest='smtp_login',
                                 help='login of the account on the SMTP server')
        self.parser.add_argument('--smtp_password',
                                 action='store',
                                 default=None,
                                 dest='smtp_password',
                                 help='password of the account on the SMTP server')
        self.parser.add_argument('--email_to',
                                 action='store',
                                 default=None,
                                 dest='email_address',
                                 help='email address (comma separated) to send the output')
        self.parser.add_argument('--email_only_on_fail',
                                 action='store_true',
                                 default=False,
                                 dest='email_only_on_fail',
                                 help='send an email only if the script to execute failed')
        self.parser.add_argument('script_to_execute',
                                 help='the script to execute')
        self.parser.add_argument('--script_args',
                                 nargs='+',
                                 dest='script_to_execute_args',
                                 default=[],
                                 help='arguments for the script to execute ')

    def parse(self, arguments):
        return self.parser.parse_args(args=arguments)


if __name__ == '__main__':
    args = ArgumentsParser().parse(sys.argv[1:])
    custom_cron = CustomCron(args)
    custom_cron.execute_script()

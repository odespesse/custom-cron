#! /usr/bin/python3
# -*- encoding: utf8 -*-

import subprocess, smtplib, os, sys
from tempfile import TemporaryFile
from email.mime.text import MIMEText
import argparse


class CustomCron(object):

    def __init__(self, args, smtp_connection=None):
        self.log_path = args.log_path
        self.email_address = args.email_address
        self.email_only_on_fail = args.email_only_on_fail
        self.smtp_connection = smtp_connection
        self.script_to_execute = args.script_to_execute
        self.script_to_execute_args = args.script_to_execute_args

    def execute_script(self):
        script_exit_code, script_output = self._execute_script()
        print(script_output)
        if self._is_log_needed():
            self._write_log(script_output)
        if self._is_email_needed():
            self._send_email(script_exit_code, script_output)

    def _execute_script(self):
        if not os.path.isfile(self.script_to_execute):
            script_output = "ERROR : Script " + self.script_to_execute + " not found\n"
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
            self.smtp_connection.quit()
            return
        subject = "[Cron : OK]" if script_exit_code == 0 else "[Cron : FAIL]"
        msg = MIMEText(script_output)
        hostname = os.uname()[1]
        msg['Subject'] = "{0} <{1}> : {2}".format(subject, hostname, self.script_to_execute)
        msg['From'] = 'custom_cron'
        msg['To'] = self.email_address
        self.smtp_connection.sendmail('custom_cron', self.email_address.split(','), msg.as_string())
        self.smtp_connection.quit()


class ArgumentsParser(object):

    def __init__(self):
        self.parser = argparse.ArgumentParser(
            description='Handle the execution of an other script in order to log and/or send the result by email')
        self.parser.add_argument('--logfile',
                                 action='store',
                                 default=None,
                                 dest='log_path',
                                 help='path where to log the output')
        self.parser.add_argument('--email',
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
        return self.parser.parse_args(args = arguments)


if __name__ == '__main__':
    args = ArgumentsParser().parse(sys.argv[1:])
    smtp_connection = smtplib.SMTP("smtp.gmail.com", 587)
    smtp_connection.ehlo()
    smtp_connection.starttls()
    smtp_connection.ehlo()
    smtp_connection.login('login', 'pwd')
    custom_cron = CustomCron(args, smtp_connection)
    custom_cron.execute_script()

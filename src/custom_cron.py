#! /usr/bin/python3
# -*- encoding: utf8 -*-

import subprocess, smtplib, os, sys
from tempfile import TemporaryFile
from email.mime.text import MIMEText
import argparse


class CustomCron(object):

	def __init__(self, args):
		self.args = args
		self.log_path = self.args.log_path
		self.email_address = self.args.email_address
		self.email_only_on_fail = self.args.email_only_on_fail
		self.script_to_execute = self.args.script_to_execute
		self.script_to_execute_args = self.args.script_to_execute_args
		self.script_output = ""
		self.script_exit_code = 1
		self.parser = None

	def is_log_needed(self):
		return self.log_path is not None

	def is_email_needed(self):
		return self.email_address is not None

	def execute_script(self):
		if os.path.isfile(self.script_to_execute):
			with TemporaryFile(mode='w+t', encoding='utf-8') as tmp_log:
				script_args = [self.script_to_execute] + self.script_to_execute_args
				self.script_exit_code = subprocess.call(script_args, stdout = tmp_log, stderr=subprocess.STDOUT)
				tmp_log.seek(0)
				self.script_output = tmp_log.read()
		else:
			self.script_output = "ERROR : Script " + self.script_to_execute + " not found\n"
		print(self.script_output)

	def write_log(self):
		with open(self.log_path, 'a', encoding='utf-8') as log:
			log.write(self.script_output)

	def send_email(self, smtp_connection):
		if self.email_only_on_fail and self.script_exit_code == 0:
			smtp_connection.quit()
			return
		if self.script_exit_code == 0:
			subject = "[Cron : OK]"
		else:
			subject = "[Cron : FAIL]"
		msg = MIMEText(self.script_output)
		hostname = os.uname()[1]
		msg['Subject'] = '%s <%s> : %s' % (subject, hostname, self.script_to_execute)
		msg['From'] = 'custom_cron'
		msg['To'] = self.email_address
		smtp_connection.sendmail('custom_cron', self.email_address.split(','), msg.as_string())
		smtp_connection.quit()


class ArgumentsParser(object):

	def __init__(self):
		self.parser = argparse.ArgumentParser(description='Handle the execution of an other script in order to log and/or send the result by email')
		self.parser.add_argument('--logfile', action='store', default = None, dest = 'log_path',
								help='path where to log the output')
		self.parser.add_argument('--email', action='store', default = None, dest = 'email_address',
								help='email address (comma separated) to send the output')
		self.parser.add_argument('--email_only_on_fail', action='store_true', default = False, dest = 'email_only_on_fail',
								help='send an email only if the script to execute failed')
		self.parser.add_argument('script_to_execute',
								help='the script to execute')
		self.parser.add_argument('--script_args', nargs='+', dest = 'script_to_execute_args', default = [],
								help='arguments for the script to execute ')

	def parse(self, arguments):
		return self.parser.parse_args(args = arguments)


if __name__ == '__main__':
	args = ArgumentsParser().parse(sys.argv[1:])
	custom_cron = CustomCron(args)
	custom_cron.execute_script()

	if custom_cron.is_log_needed():
		custom_cron.write_log()

	if custom_cron.is_email_needed():
		smtp_connection = smtplib.SMTP("smtp.gmail.com", 587)
		smtp_connection.ehlo()
		smtp_connection.starttls()
		smtp_connection.ehlo()
		smtp_connection.login('login', 'pwd')
		custom_cron.send_email(smtp_connection)

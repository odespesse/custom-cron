#! /usr/bin/python
# -*- encoding: utf8 -*-

import subprocess, sys, smtplib, os
from tempfile import TemporaryFile
from email.mime.text import MIMEText

class CustomCron(object):

	MIN_ARGS_NUMBER = 4

	def __init__(self, args):
		self.args = args
		self.log_path = None
		self.email_address = None
		self.script_to_execute = None
		self.script_to_execute_args = []
		self.script_output = ""
		self.script_exit_code = 0

	def is_not_enough_args(self):
		return len(self.args) < CustomCron.MIN_ARGS_NUMBER

	def parse_arguments(self):
		self.log_path = self.args[1] if self.args[1] != "NO_LOG" else None
		self.email_address = self.args[2] if self.args[2] != "NO_MAIL" else None
		script_to_execute_position = 3
		self.script_to_execute = self.args[script_to_execute_position]
		args_start_position = 4
		for i in xrange(args_start_position, len(self.args)):
			self.script_to_execute_args.append(self.args[i])

	def is_log_needed(self):
		return self.log_path is not None

	def is_email_needed(self):
		return self.email_address is not None

	def execute_script(self):
		if os.path.isfile(self.script_to_execute):
			with TemporaryFile() as tmp_log:
				script_args = [self.script_to_execute] + self.script_to_execute_args
				self.script_exit_code = subprocess.call(script_args, stdout = tmp_log, stderr=subprocess.STDOUT)
				tmp_log.seek(0)
				self.script_output = tmp_log.read()
		else:
			self.script_output = "ERROR : Script " + self.script_to_execute + " not found\n"

	def write_log(self):
		with open(self.log_path, 'a') as log:
			log.write(self.script_output)

	def send_email(self, smtp_connection):
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

if __name__ == '__main__':
	custom_cron = CustomCron(sys.argv)

	if custom_cron.is_not_enough_args():
		print "Usage : log_path dest_mail script_path srcipt_args*"
		sys.exit(1)

	custom_cron.parse_arguments()
	custom_cron.execute_script()

	if custom_cron.is_log_needed():
		custom_cron.write_log()

	if custom_cron.is_email_needed():
		smtp_connection = smtplib.SMTP("smtp.gmail.com",587)
		smtp_connection.ehlo()
		smtp_connection.starttls()
		smtp_connection.ehlo()
		smtp_connection.login('login', 'pwd')
		custom_cron.send_email(smtp_connection)

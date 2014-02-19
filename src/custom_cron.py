#! /usr/bin/python
# -*- encoding: utf8 -*-

import subprocess, sys, smtplib, os
from tempfile import mkstemp
from email.mime.text import MIMEText

class CustomCron(object):

	MIN_ARGS_NUMBER = 3

	def __init__(self, args):
		self.args = args
		self.log_path = None
		self.email_address = None
		self.script_to_execute = None
		self.script_to_execute_args = []

	def is_not_enough_args(self):
		return len(self.args) < CustomCron.MIN_ARGS_NUMBER

	def parse_arguments(self):
		self.log_path = self.args[0] if self.args[0] != "NO_LOG" else None
		self.email_address = self.args[1] if self.args[1] != "NO_MAIL" else None
		script_to_execute_position = 2
		self.script_to_execute = self.args[script_to_execute_position]
		args_start_position = 3
		for i in xrange(args_start_position, len(self.args)):
			self.script_to_execute_args.append(self.args[i])

	def is_log_needed(self):
		return self.log_path is not None

	def is_email_needed(self):
		return self.email_address is not None

if __name__ == '__main__':
	custom_cron = CustomCron(sys.argv)

	if custom_cron.is_not_enough_args():
		print "Usage : log_path dest_mail script_path srcipt_args*"
		sys.exit(1)

	custom_cron.parse_arguments()

	_, tmp_name = mkstemp(text=True)
	tmp_log = open(tmp_name,'w')

	script_args = []
	for i in xrange(3, len(sys.argv)):
		script_args.append(sys.argv[i])

	if os.path.isfile(custom_cron.script_to_execute):
		script_ret = subprocess.call(script_args, stdout=tmp_log, stderr=subprocess.STDOUT)
	else:
		script_ret = 1

	tmp_log_read = open(tmp_name, 'r')
	script_output = tmp_log_read.read()

	if custom_cron.is_log_needed():
		with open(custom_cron.log_path,'a') as log:
			log.write(script_output)

	if custom_cron.is_email_needed():
		msg = MIMEText(script_output)

		if script_ret == 0:
			status = "[CRON : OK]"
		else:
			status = "[CRON : FAIL]"

		hostname = os.uname()[1]
		msg['Subject'] = '%s <%s> : %s' % (status, hostname, custom_cron.script_to_execute)
		# msg['From'] = me
		msg['To'] = custom_cron.email_address

		# Send the message via our own SMTP server, but don't include the
		# envelope header.
		# s = smtplib.SMTP('localhost')
		# s.sendmail(me, [you], msg.as_string())
		# s.quit()

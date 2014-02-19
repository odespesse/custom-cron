#! /usr/bin/python
# -*- encoding: utf8 -*-

import subprocess, sys, smtplib, os
from tempfile import mkstemp
from email.mime.text import MIMEText

class CustomCron(object):

	MIN_ARGS_NUMBER = 3

	def __init__(self, args):
		self.args = args

	def is_not_enough_args(self):
		return len(self.args) < CustomCron.MIN_ARGS_NUMBER

if __name__ == '__main__':
	c = CustomCron(sys.argv)

	if c.is_not_enough_args():
		print "Usage : log_path dest_mail script_path srcipt_args*"
		sys.exit(1)

	_, tmp_name = mkstemp(text=True)
	tmp_log = open(tmp_name,'w')

	script_args = []
	for i in xrange(3, len(sys.argv)):
		script_args.append(sys.argv[i])

	script_to_execute = sys.argv[3]
	if os.path.isfile(script_to_execute):
		script_ret = subprocess.call(script_args, stdout=tmp_log, stderr=subprocess.STDOUT)
	else:
		script_ret = 1

	tmp_log_read = open(tmp_name, 'r')
	script_output = tmp_log_read.read()

	log_path = sys.argv[1]
	if log_path != "NO_LOG":
		with open(log_path,'a') as log:
			log.write(script_output)

	mail_dest = sys.argv[2]
	if mail_dest != "NO_MAIL":
		msg = MIMEText(script_output)

		if script_ret == 0:
			status = "[CRON : OK]"
		else:
			status = "[CRON : FAIL]"

		hostname = os.uname()[1]
		msg['Subject'] = '%s <%s> : %s' % (status, hostname, script_to_execute)
		# msg['From'] = me
		msg['To'] = mail_dest

		# Send the message via our own SMTP server, but don't include the
		# envelope header.
		# s = smtplib.SMTP('localhost')
		# s.sendmail(me, [you], msg.as_string())
		# s.quit()

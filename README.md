# Custom Cron

On Unix systems, Cron is perfect to execute scheduled command but the only way to log the command output is by email.
This limitation is a problem if your email server isn't reliable or if you want to customize the email content.
Custom Cron implement a lightweight wrapper which handle the execution of the command.

## Setup

You'll need a Python environment >= 2.7. 
Then you need to copy the file custom_cron.py on your system and make sure it is executable :

	$ chmod u+x custom_cron.py

## Options

Handle the execution of an other script in order to log and/or send the result by email

	custom_cron.py \[-h\] \[--logfile LOG_PATH\] \[--email EMAIL_ADDRESS\]
	               \[--script_args SCRIPT_TO_EXECUTE_ARGS \[SCRIPT_TO_EXECUTE_ARGS ...\]\]
			script_to_execute

	-h
		help message

	--logfile 
		path where to log the output

	--email
		email address (comma separated) to send the output

	script_to_execute
		the script to execute

	--script_args
		arguments for the script to execute

## Usage

Set your crontab as usual, but instead execute custom_cron.py with your command as argument.
For instance, if you want to execute my_script.sh as root every hour you must write in your crontab :

	* */1 * * * root /path/to/custom_cron.py /other/path/to/my_script.py

If you want the output to be logged in file.log just write :

	* */1 * * * root /path/to/custom_cron.py --logfile /path/to/file.log /other/path/to/my_script.py

If the script need arguments (foo, bar and "hello world) to be passed and say you want the output to be sent at your@email.com write :

	* */1 * * * root /path/to/custom_cron.py --email your@email.com /other/path/to/my_script.py --script_args foo bar "hello world"
or

	* */1 * * * root /path/to/custom_cron.py --email your@email.com --script_args foo bar "hello world" -- /other/path/to/my_script.py

## License

GNU GENERAL PUBLIC LICENSE Version 3

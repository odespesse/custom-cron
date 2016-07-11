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

	custom_cron.py \[-h\] \[\--configuration CONFIGURATION_PATH\] \[--logfile LOG_PATH\] \[--email EMAIL_ADDRESS\]
	               \[--script_args SCRIPT_TO_EXECUTE_ARGS \[SCRIPT_TO_EXECUTE_ARGS ...\]\]
			script_to_execute

	-h
		help message

    --configuration
        path to the configuration file

	--logfile 
		path where to log the output

	--email
		email address (comma separated) to send the output

	--email_only_on_fail
		do not send an email if the script to execute ended successfully

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

Although you already could send an email with cron the subject of the email isn't particularly useful.
Custom Cron will send an email subject like :

	[Execution result] <hostname> command

the execution result could be [Cron : OK] if the command returned 0 or [Cron : Fail] otherwise.
As soon as you receive the email you will be able to know if you need to take a look at it immediately because of an error or if it can wait.

## Configuration file

If you have to many arguments, you can simplify the script configuration by putting everything inside a file.
The file is in a simple INI format. You just need to write a file like this (let's name it "configuration.ini") :

    [script]
    path = ./hello.sh
    arguments = Hello world

    [log]
    path = /tmp/log

    [email]
    to = your@email.com
    only_on_fail = no

Then you just need to tell where to find this configuration :

    * */1 * * * root /path/to/custom_cron.py --configuration /other/path/to/configuration.ini

## License

GNU GENERAL PUBLIC LICENSE Version 3

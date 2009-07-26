[director]
# The broker connection details:
msg_host = "127.0.0.1"
msg_port = 61613
msg_username = ''
msg_password = ''
msg_channel = 'evasion'

[broker]
disabled = 'no'
order = 1
controller = 'director.controllers.commandline'
command = "python scripts/morbidsvr -p 61613 -i 127.0.0.1"
workingdir = "."

[agencyhq]
disabled = 'yes'
order = 2
controller = 'director.controllers.agencyhq'

[viewpoint]
disabled = 'yes'
order = 3
controller = 'director.controllers.viewpoint'
xulrunner = "xulrunner"
args = "-nofullscreen yes -starturi http://localhost:9808/"

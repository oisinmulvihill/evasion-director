[director]
# The broker connection details:
msg_host = "127.0.0.1"
msg_port = 61613
msg_username = ''
msg_password = ''
msg_channel = 'evasion'
disable_broker = ${disable_broker}

[broker]
disabled = 'no'
order = 1
controller = 'director.controllers.commandline'
command = "python scripts//morbidsvr -p 61613 -i 127.0.0.1"
workingdir = "${install_dir}"


[agencyhq]
disabled = '${disable_agency}'
order = 2
controller = 'director.controllers.agencyhq'

[testagent]
# Example of an agent entry
alias = 1
cat = 'service'
agent = 'agency.agents.testing.fake'


# Example of starting a third-party web application:
[yourwebapp]
disabled = 'yes'
order = 3
controller = 'director.controllers.commandline'
command = "yourwebapp start cmd: start-app.exe"
workingdir = "${install_dir}"


[viewpoint]
#disabled = 'yes'
order = 4
controller = 'director.controllers.viewpoint'
xulrunner = "xulrunner"
uri = "http://localhost:9808/"
args = "-nofullscreen yes"

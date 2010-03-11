[director]
msg_channel = 'evasion'
internal_broker = 'yes'

[agencyhq]
disabled = '${disable_agency}'
order = 2
controller = 'director.controllers.agencyctrl'

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


#
# Logging
#
[loggers]
keys=root

[handlers]
keys=default

[formatters]
keys=default


[logger_root]
level=NOTSET
handlers=default
qualname=(root)
propagate=1
channel=
parent=

[handler_default]
class=StreamHandler
args=(sys.stdout,)
level=INFO
formatter=default


# Usefull alternative: log to file which rotates.
#
#[handler_default]
#class=handlers.RotatingFileHandler
#args=("director.log", "au", 10 * 1024 * 1024, 2)
#level=INFO
#formatter=default


[formatter_default]
format=%(asctime)s %(name)s %(levelname)s %(message)s
datefmt=


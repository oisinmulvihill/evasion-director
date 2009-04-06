
[director]
# If this doesn't exist then logging to standard out is done:
logconfig = "${director_log_cfg}"
logdir = "${log_dir}"

# This is the command line used to launch the web presence:
app = "${python_exe} ${install_home}\Scripts\paster serve development.ini"

# This is the directory to run the app from:
app_dir = "${install_home}"

# deviceaccess program:
devicemain = "${python_exe} ${install_home}\Scripts\manager --logconfig="${manager_log_cfg}" --config=${da_config} --dmconfig=${manager_config}"

# where to run the deviceaccess from:
devicemaindir = "${install_home}"

# This is the command used to invoke the xulrunner exe:
xulrunner =  "xulrunner"

# This is the XUL browser config xulrunner should be using:
#
# Live command line
browser = "${viewpoint_path}\application.ini"

# This is the time, in seconds, the app manager waits before 
# checking that the xul browser or the web presence is still 
# running. 
poll_time = 1


# This is the MorbidQ (http://www.morbidq.com/) replacement
# for Apache ActiveMQ. This is a simple python implementation
# stomp broker. 
#
# The command line to run:
brokermain = "${python_exe} ${install_home}/scripts/morbidsvr"

# This isn't really important as MorbidQ should be installed
# in python. I'm just running it from here in case it needs
# to output any files.
brokermaindir = "${install_home}"


# If this is present, then the director will not run the
# web presence on a random free port. It will always use the
# port specified by fix_port. If the port is not fixed then
# the random free port will be used to direct the xul browser
# to the web presence new port. Nothing in the code should
# rely on http://localhost:9808 as this could change if fix
# port is not set.
#fix_port = 9808


# Disable the STOMP Broker.
#
disable_broker = "${disable_broker}"


# Disable the app.
#
disable_app = "${disable_app}"
fix_port = 5000


# Disable the XUL Browser app for testing purposes. If set to 'no'
# then the director will start and manage the XUL app. If
# this is 'yes' then acceptance testing with firefox is 
# being done.
#
disable_xul = "${disable_xul}"

# Disable the deviceaccess app for testing purposes. If set 
# to 'no' then the director will start and manage the 
# deviceaccess as normal. 
#
disable_deviceaccess = "${disable_device}"


# This is the location and auth details of the ActiveMQ/STOMP 
# broker server. You should make sure all parts of the system 
# are using the same message broker.
#
msg_host = "127.0.0.1"
msg_port = 61613
msg_username = ''
msg_password = ''
msg_channel = 'evasion'

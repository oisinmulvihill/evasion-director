
[director]
# If this doesn't exist then logging to standard out is done:
logconfig = "${director_log_cfg}"
logdir = "${log_dir}"

# This is the command line used to launch the web application:
app = "${python_exe} ${install_home}\Scripts\paster serve development.ini"

# This is the directory to run the app from:
app_dir = "${install_home}"

# Disable the app? "yes" | "no"
#
disable_app = "${disable_app}"
fix_port = 5000


# This is the command line used to launch the optional app. 
#
# This should produce crossbow core relative to the current location
#app2 = "c:\FDS\services\crossbow_core\crossbow_core.exe"
#app2_dir = "c:\FDS\services\crossbow_core"
#
app2 = " ${install_home}\..\crossbow_core\crossbow_core.exe"
app2_dir = "${install_home}\..\crossbow_core"


# Disable the optional app? "yes" | "no"
#
disable_app2 = "${disable_app2}"


# deviceaccess program:
devicemain = "${python_exe} ${install_home}\Scripts\manager --logconfig="${manager_log_cfg}" --config=${da_config} --dmconfig=${manager_config}"

# where to run the deviceaccess from:
devicemaindir = "${install_home}"

# Disable the deviceaccess app for testing purposes. If set 
# to 'no' then the director will start and manage the 
# deviceaccess as normal. 
#
disable_deviceaccess = "${disable_device}"


# This is the command used to invoke the xulrunner exe:
xulrunner =  "xulrunner"

# This is the XUL browser config xulrunner should be using:
#
# Live command line
browser = "${viewpoint_path}\application.ini"

# Disable the viewpoint app for testing purposes. If set to 'no'
# then the director will start and manage the XUL app. If
# this is 'yes' then acceptance testing with firefox is 
# being done.
#
disable_xul = "${disable_xul}"


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

# Disable the STOMP Broker.
#
disable_broker = "${disable_broker}"

# This is the location and auth details of the broker server. 
# You should make sure all parts of the system are using the 
# same message broker and channel.
#
msg_host = "127.0.0.1"
msg_port = 61613
msg_username = ''
msg_password = ''
msg_channel = 'evasion'


# Prevent director busy waiting. This just limits the time 
# between maintenances checks.
poll_time = 1

; Director template service configuration.
;
; The servicestation.exe may require vc2008 redistributables 
; to run on the target system. It will not run on win9x 
; based computers. Only computers with win2k onwards will be
; able to run servicestation.exe
;
; The service is installed as follows:
;
;   servicestation.exe -c <absolute path to config.ini> -i
;
; The service can be uninstalled as follows:
;
;   servicestation.exe -c <absolute path to config.ini> -i
;
; Multiple instances of the service can be run as long as each 
; servicestation.exe is put into its own directory. There is
; no requirement for the config.ini to be in the same directory
; as the exe.
;
; Oisin Mulvihill
; 2009-03-19
;
[service]
; The servce name and display name of the service:
name = EvasionDirector

; The command line to run for this service:
command_line = ${exe} --config=${director_cfg} --logconfig=${logconfig_filename} 

; The directory to run the command_line from. No double 
; slashes are needed. For example c:\temp is ok however 
; c:\\temp is not.
working_dir = ${servicestation_dir}

; Not yet used: will eventually log STDERR/OUT to a file at 
; the moment it is thrown away.
;log_file = 

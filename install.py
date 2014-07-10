#!/usr/bin/env python

"""
Installs alignreads and its dependencies.
"""
#Generic Imports
import os, string, sys, time, copy, re
import argparse

#Specific Imports
import subprocess
import logging

#Change log
change_log = [('1.0.0',		'First version of the script')]
version = change_log[-1][0]

#Constants
program_description = "%s\nVersion: %s" % (__doc__, version)
accepted_lastz_versions = ['1.3.2', '1.03.02']
accepted_readtools_versions = ['1.0.0']
accepted_makeconesnsus_versions = ['1.1.1']
accepted_runyasra_versions = ['2.2.3']
accepted_nucmer_versions = ['3.1']
installation_folder = os.path.abspath(os.getcwd())
default_executable_folder = os.path.join(installation_folder, 'bin')

#Initialization
logging.basicConfig()


###Command Line Parser Initilization###
command_line_parser = argparse.ArgumentParser(description=program_description)
command_line_parser.add_argument('-i', '--not-interactive', default=True, action="store_false", dest="interactive",\
                               help="Do not prompt user for input during installation. Recommended and default settings will be used unless otherwise specified by command line arguments.")
command_line_parser.add_argument("-p", '--python', nargs='?', default=None,\
                               help="Specify the path to nucmer. (Default: attempt to find path automatically). ")
command_line_parser.add_argument("-n", '--nucmer', nargs='?', default=None,\
                               help="Specify the path to nucmer. (Default: attempt to find path automatically). ")
command_line_parser.add_argument("-l", '--lastz', nargs='?', default=False,\
                               help="Specify the path to lastz. If the option is used, but no path given, an attempt will be made to find the path automatically. (Default: download and install automatically). ")
command_line_parser.add_argument("-y", '--yasra', nargs='?', default=False,\
                               help="Specify the path to YASRA. If the option is used, but no path given, an attempt will be made to find the path automatically. (Default: download and install automatically). ")
command_line_parser.add_argument('-e', '--executable_path',\
                               help='Path to store any automatically installed binaries.')
arguments = command_line_parser.parse_args()

#Validation of program paths
def generic_program_validation(path, accepted_versions):
    try:
        name = os.path.split(path)[1]
        output =  subprocess.check_output([path, "-v"], stderr = subprocess.STDOUT)
        version = re.search('version ([0123456789.]+)', output).group(1)
        if version not in accepted_versions:
            raise TypeError("Wrong version of %s detected. Version found: '%s'.  Compatible Versions: '%s'" %\
                                                 (name, version, ", ".join(accepted_versions)))
    except:
        logging.fatal('An unknown error occurred during validation of %s:' % name)
        raise

def find_active_version(name):
    path = subprocess.check_output(['which', name], stderr = subprocess.STDOUT)
    if os.path.exists(path):
		output =  subprocess.check_output([path, "-v"], stderr = subprocess.STDOUT)
		version = re.search('version ([0123456789.]+)', output).group(1)
        return (path, version)
    else:
        return None

if arguments.lastz is False:
	install_lastz(install_path, executable_path=arguments.executable_path, interactive=arguments.interactive)
elif arguments.lastz is None:
    arguments.lastz, lastz_version = find_active_version('lastz')
    if arguments.lastz is None:
        raise TypeError('Cannot locate lastz. Specifcy location using option --lastz or omit option to download and install automatically.')
    else:
        print "Found lastz %s at %s" % (lastz_version, arguments.lastz)
generic_program_validation(arguments.lastz, accepted_lastz_versions)
    
if options.nucmer is None:
    options.nucmer, nucmer_version = find_active_version('nucmer')
    if options.nucmer is None:
        raise TypeError('Cannot locate nucmer. Specifcy location using option --nucmer.')
    else:
        print "Found nucmer %s at %s" % (nucmer_version, options.nucmer)
generic_program_validation(options.nucmer, accepted_nucmer_versions)

if options.python is None:
    options.python, python_version = find_active_version('python')
    if options.python is None:
        raise TypeError('Cannot locate python. Use option -l/--python-location')
    else:
        print "Found python %s at %s" % (python_version, options.python)
######

### Unpack Installation ###
process = Popen(['tar', '-xvf', 'uninstalled_content.tar'], stdout=PIPE)
process.wait()
for name in os.listdir(os.path.join(installation_folder, 'uninstalled_content')):
    os.rename(os.path.join(installation_folder, 'uninstalled_content', name), os.path.join(installation_folder, name))
os.rmdir(os.path.join(installation_folder, 'uninstalled_content'))
######

### Modify Default Configuration File ###
config_path = os.path.join(installation_folder, 'default_configuration.py')
with open(config_path, 'r') as config_handle:
    config = config_handle.read()
config = config.replace('yasra_location = None', 'yasra_location = "%s"' % yasra_location)
config = config.replace('nucmer_location = None', 'nucmer_location = "%s"' % options.nucmer)
config = config.replace('python_location = None', 'python_location = "%s"' % options.python)
config = config.replace('lastz_location = None', 'lastz_location = "%s"' % options.lastz)
with open(config_path, 'w') as config_handle:
    config_handle.write(config)
######

### Create Shell Script to Run Alignreads ###
alignreads_location = os.path.join(installation_folder, 'alignreads.py')
shell_script_location = os.path.join(installation_folder, 'alignreads')
shell_text = '#!/bin/csh\n%s %s $*\n' % (options.python_location, alignreads_location)
with open(shell_script_location, 'w') as shell_handle:
    shell_handle.write(shell_text)
process = Popen(['chmod', '+x', shell_script_location], stdout=PIPE)
process.wait()
######

### Set User Shell PATH ###
if options.shell_init_file is not None:
    try:
        shell_string = 'setenv PATH {$PATH}:%s   #Automatically added during installation of alignreads\n' % installation_folder
        with open(options.shell_init_file, 'r') as handle:
            cshrc_file = handle.read()
        if shell_string not in cshrc_file:
            with open(options.shell_init_file, 'a') as handle:
                handle.write(shell_string)
        else:
            print 'Note: This installation is already in the search path'
    except:
        raise
    else:
        print 'Your shell search path has been set to include the alignreads installation.\n'+\
        'This has been done by adding a line to your .cshrc file.\n'+\
        'You must relogin before the search path changes take effect'
######
print 'The installation has completed successfully.'
        

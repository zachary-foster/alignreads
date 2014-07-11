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
installer_folder = os.path.abspath(os.getcwd())
default_executable_folder = os.path.join(installation_folder, 'bin')

#Initialization
logging.basicConfig()


#Command line parsing
command_line_parser = argparse.ArgumentParser(description=program_description)
command_line_parser.add_argument("install_path",\
								help="Location to install alignreads.")
command_line_parser.add_argument('-i', '--not-interactive', default=True, action="store_false", dest="interactive",\
								help="Do not prompt user for input during installation. Recommended and default settings will be used unless otherwise specified by command line arguments.")
command_line_parser.add_argument("-p", '--python', nargs='?', default=None,\
								help="Specify the path to nucmer. (Default: attempt to find path automatically). ")
command_line_parser.add_argument("-n", '--nucmer', nargs='?', default=False,\
								help="Specify the path to nucmer. (Default: attempt to find path automatically). ")
command_line_parser.add_argument("-l", '--lastz', nargs='?', default=False,\
								help="Specify the path to lastz. If the option is used, but no path given, an attempt will be made to find the path automatically. (Default: download and install automatically). ")
command_line_parser.add_argument("-y", '--yasra', default=False,\
								help="Specify the path to YASRA. If the option is used, but no path given, an attempt will be made to find the path automatically. (Default: download and install automatically). ")
command_line_parser.add_argument('-e', '--executable_path',\
								help='Path to store any automatically installed binaries.')
arguments = command_line_parser.parse_args()

#Make installation directory
os.mkdir(arguments.install_path)

#Unpack Installation
uninstalled_content_path = os.path.join(installer_folder, 'uninstalled_content.tar')
tar_handle = tarfile.open(uninstalled_content_path, 'r')
tar_handle.extractall(arguments.install_path)
tar_handle.close()
for name in os.listdir(uninstalled_content_path):
	os.rename(os.path.join(uninstalled_content_path, name), os.path.join(arguments.install_path, name))
os.rmdir(os.path.join(installation_folder, 'uninstalled_content'))

#Validation and installation of requirements
if arguments.python is None:
	arguments.python, python_version = find_active_version('python')
	if options.python is None:
		raise TypeError('Cannot locate python. Use option -l/--python-location')
	else:
		print "Found python %s at %s" % (python_version, options.python)

if arguments.lastz is False:
	install_lastz(install_path, executable_path=arguments.executable_path, interactive=arguments.interactive)
	arguments.lastz = install_path
elif arguments.lastz is None:
	arguments.lastz, lastz_version = find_active_version('lastz')
	if arguments.lastz is None:
		raise TypeError('Cannot locate lastz. Specifcy location using option --lastz or omit option to download and install automatically.')
	else:
		print "Found lastz %s at %s" % (lastz_version, arguments.lastz)
generic_program_validation(arguments.lastz, accepted_lastz_versions)

if arguments.yasra is False:
	install_yasra(install_path, executable_path=arguments.executable_path, interactive=arguments.interactive)
	arguments.yasra = install_path

if arguments.nucmer is False:
	install_nucmer(install_path, executable_path=arguments.executable_path, interactive=arguments.interactive)
	arguments.nucmer = install_path
elif options.nucmer is None:
	options.nucmer, nucmer_version = find_active_version('nucmer')
	if options.nucmer is None:
		raise TypeError('Cannot locate nucmer. Specifcy location using option --nucmer.')
	else:
		print "Found nucmer %s at %s" % (nucmer_version, options.nucmer)
generic_program_validation(options.nucmer, accepted_nucmer_versions)

#Modify Default Configuration File
config_path = os.path.join(arguments.install_path, 'default_configuration.py')
with open(config_path, 'r') as config_handle:
	config = config_handle.read()
config = config.replace('yasra_location = None', 'yasra_location = "%s"' % arguments.yasra)
config = config.replace('nucmer_location = None', 'nucmer_location = "%s"' % arguments.nucmer)
config = config.replace('python_location = None', 'python_location = "%s"' % arguments.python)
config = config.replace('lastz_location = None', 'lastz_location = "%s"' % arguments.lastz)
with open(config_path, 'w') as config_handle:
	config_handle.write(config)

#Create Shell Script to Run Alignreads
alignreads_location = os.path.join(arguments.install_path, 'alignreads.py')
shell_script_location = os.path.join(arguments.install_path, 'alignreads')
shell_text = '#!/bin/csh\n%s %s $*\n' % (options.python, alignreads_location)
with open(shell_script_location, 'w') as shell_handle:
	shell_handle.write(shell_text)
subprocess.call(['chmod', '+x', shell_script_location], stdout = runtime_output_handle, stderr = subprocess.STDOUT)

print 'The installation has completed successfully.'

#Functions
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

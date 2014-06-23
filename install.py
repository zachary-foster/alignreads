### Imports ###
import os, string, sys, time, copy, re
from optparse import *
from subprocess import *
import logging
######

### Variable Initialization ###
logging.basicConfig()
program_arguments = sys.argv #argument list supplied by user in its raw form
minimum_argument_number = 1 #the smallest amount of arguments with which it is possible to run the script
original_cwd = os.getcwd()
program_name = 'install'
program_version = '1.0.0'
program_usage = 'python %s.py <Path to YASRA folder> [options]' % (program_name)
accepted_lastz_versions = ['1.3.2', '1.03.02']
accepted_readtools_versions = ['1.0.0']
accepted_makeconesnsus_versions = ['1.1.1']
accepted_runyasra_versions = ['2.2.3']
accepted_nucmer_versions = ['3.1']
######

###Command Line Parser Initilization###
command_line_parser = OptionParser(usage = program_usage, version = "Version %s" % program_version)
command_line_parser.add_option("-l", '--lastz-location', action='store', default=None, type='string', metavar='PATH',\
                               help="Specify the path to lastz. (Default: attempt to find automatically)")
command_line_parser.add_option("-n", '--nucmer-location', action='store', default=None, type='string', metavar='PATH',\
                               help="Specify the path to nucmer. (Default: attempt to find automatically)")
command_line_parser.add_option("-p", '--python-location', action='store', default=None, type='string', metavar='PATH',\
                               help="Specify the path to python. (Default: attempt to find automatically)")
command_line_parser.add_option("-i", '--shell-init-file', action='store', default=None, type='string', metavar='PATH',\
                               help="Specify the path to your .cshrc / .tcshrc file so the alignreads installation can be added to you search $PATH. (Default: attempt to find automatically)")
(options, arguments) = command_line_parser.parse_args(sys.argv[1:])
if len(arguments) == 0: #if no arguments are supplied
    command_line_parser.print_help()
    sys.exit(0)
yasra_location = arguments[0]
if os.path.exists(yasra_location) is False:
    raise TypeError('Invalid path to YASRA: %s' % yasra_location)
######

### Validation of program paths ###
def generic_program_validation(path, accepted_versions):
    try:
        name = os.path.split(path)[1]
        process = Popen([path, "-v"], shell=False, stdout=PIPE, stdin=PIPE, stderr=STDOUT, close_fds=True)
        process.wait()
        output = process.stdout.read()
        version = re.search('version ([0123456789.]*)', output).group(1)
        if version not in accepted_versions:
            raise TypeError("Wrong version of %s detected. Version found: '%s'.  Compatible Versions: '%s'" %\
                                                 (name, version, ", ".join(accepted_versions)))
    except:
        logging.fatal('An unknown error occurred during validation of %s:' % name)
        raise

def find_active_version(name):
    process = Popen(['which', name], stdout=PIPE)
    process.wait()
    output = process.communicate()[0].strip()
    if os.path.exists(output):
        return output
    else:
        return None

if options.lastz_location is None:
    options.lastz_location = find_active_version('lastz')
    if options.lastz_location is None:
        raise TypeError('Cannot locate lastz. Use option -l/--lastz-location')
    else:
        print "Found lastz at %s" % options.lastz_location
generic_program_validation(options.lastz_location, accepted_lastz_versions)
    
if options.nucmer_location is None:
    options.nucmer_location = find_active_version('nucmer')
    if options.nucmer_location is None:
        raise TypeError('Cannot locate nucmer. Use option -l/--nucmer-location')
    else:
        print "Found nucmer at %s" % options.nucmer_location
generic_program_validation(options.nucmer_location, accepted_nucmer_versions)

if options.python_location is None:
    options.python_location = find_active_version('python')
    if options.python_location is None:
        raise TypeError('Cannot locate python. Use option -l/--python-location')
    else:
        print "Found python at %s" % options.python_location
######

### Unpack Installation ###
installation_folder = os.path.abspath(os.getcwd())
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
config = config.replace('nucmer_location = None', 'nucmer_location = "%s"' % options.nucmer_location)
config = config.replace('python_location = None', 'python_location = "%s"' % options.python_location)
config = config.replace('lastz_location = None', 'lastz_location = "%s"' % options.lastz_location)
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
        

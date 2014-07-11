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
import urllib2
import tarfile
import shutil
from urlparse import urlsplit, urlunsplit

#Functions
def generic_program_validation(path, accepted_versions):
	try:
		name = os.path.split(path)[1]
		process =  subprocess.Popen([path, "-v"], stderr = subprocess.STDOUT, stdout=subprocess.PIPE)
		output = process.communicate()[0]
		version = re.search('version ([0123456789.]+)', output).group(1)
		if version not in accepted_versions:
			raise TypeError("Wrong version of %s detected. Version found: '%s'.  Compatible Versions: '%s'" %\
												 (name, version, ", ".join(accepted_versions)))
	except:
		logging.fatal('An unknown error occurred during validation of %s:' % name)
		raise

def find_active_version(name):
	path = subprocess.check_output(['which', name], stderr = subprocess.STDOUT).strip()
	if os.path.exists(path):
		process =  subprocess.Popen([path, "-v"], stderr = subprocess.STDOUT, stdout=subprocess.PIPE)
		output = process.communicate()[0]
		version = re.search('version ([0123456789.]+)', output).group(1)
		return (path, version)
	else:
		return None

#From: http://codereview.stackexchange.com/questions/13027/joining-url-path-components-intelligently
def url_path_join(*parts):
	"""Normalize url parts and join them with a slash."""
	def first(sequence, default=''):
		return next((x for x in sequence if x), default)
	schemes, netlocs, paths, queries, fragments = zip(*(urlsplit(part) for part in parts))
	scheme = first(schemes)
	netloc = first(netlocs)
	path = '/'.join(x.strip('/') for x in paths if x)
	query = first(queries)
	fragment = first(fragments)
	return urlunsplit((scheme, netloc, path, query, fragment))
 
def get_links(url):
	# From: http://www.diveintopython.net/html_processing/extracting_data.html
	from sgmllib import SGMLParser
	class url_lister(SGMLParser):
		def reset(self):                              
			SGMLParser.reset(self)
			self.urls = []
		def start_a(self, attrs):                    
			href = [v for k, v in attrs if k=='href'] 
			if href:
				self.urls.extend(href)
	url_handle = urllib2.urlopen(url)
	link_parser = url_lister()
	link_parser.feed(url_handle.read())
	url_handle.close()
	link_parser.close()
	return [url for url in link_parser.urls]

def get_yasra_versions(site_url):
	files = get_links(site_url)
	yasra_files = [f for f in files if re.match(r"YASRA-\d+\.\d+\.tar\.gz", f)]
	return yasra_files
	
def download_yasra(install_path, file_name=None, interactive=True, recommended_version="YASRA-2.33.tar.gz"):
	site_url = "http://www.bx.psu.edu/miller_lab/dist"
	yasra_versions = get_yasra_versions(site_url)
	yasra_versions.sort(key=lambda x: map(int, re.match(r"YASRA-(\d+\.\d+)\.tar\.gz", x).group(1).split('.')))
	yasra_versions.reverse()
	if interactive:
		input_is_accepted = False
		while input_is_accepted == False:
			prompt_header = "Multiple versions of YASRA are available. Enter the number corresponding to the version you want to download..."
			prompt_versions = ["   %d: %s" % (i + 1, yasra_versions[i]) for i in range(0, len(yasra_versions))]
			if recommended_version in yasra_versions:
				prompt_versions[yasra_versions.index(recommended_version)] += " (recommended)"
			prompt_lines = [prompt_header] + prompt_versions
			prompt = '\n'.join(prompt_lines)
			user_input = raw_input(prompt + '\n')
			try: 
				user_selection = int(user_input)
			except ValueError:
				print("Invalid selection. Try again..")
				continue
			else:
				input_is_accepted = True
			version_to_download = yasra_versions[user_selection - 1]
	else:
		if recommended_version not in yasra_versions:
			raise RuntimeError('Could not locate yasra version "%s" at "%s". You can try the interactive installation option to see if other versions are available.' % (recommended_version, site_url))
		if yasra_versions[0] != recommended_version:
			print('NOTE: the recommended version to be installed "%s" is not the newest version. "%s" appears to be the newest.' % (recommended_version, yasra_versions[0]))
		version_to_download = recommended_version
	if file_name == None:
		file_name = version_to_download
	version_to_download_url = url_path_join(site_url, version_to_download)
	output_path = os.path.join(install_path, file_name)
	print('Downloading "%s"...' % version_to_download_url)
	download_handle = urllib2.urlopen(version_to_download_url)
	with open(output_path, 'wb') as output_handle:
		output_handle.write(download_handle.read())
	download_handle.close()
	return output_path

def get_dev_lastz_versions(site_url):
	files = get_links(site_url)
	matches = [re.match(r".*(lastz-\d+\.\d+\.\d+\.tar\.gz)", f) for f in files]
	lastz_files = [m.group(1) for m in matches if m]
	return lastz_files

def get_lastz_versions(site_url):
	files = get_links(site_url)
	lastz_files = [f for f in files if re.match(r"lastz-(\d+\.\d+\.\d+)\.tar\.gz", f)]
	return lastz_files


def download_lastz(install_path, file_name=None, interactive=True, recommended_version="lastz-1.03.02.tar.gz"):
	old_site_url = "http://www.bx.psu.edu/miller_lab/dist"
	dev_site_url = "http://www.bx.psu.edu/~rsharris/lastz/newer"
	old_lastz_versions = get_lastz_versions(old_site_url)
	dev_lastz_versions = get_dev_lastz_versions(dev_site_url)
	lastz_versions = old_lastz_versions + dev_lastz_versions
	lastz_versions.sort(key=lambda x: map(int, re.match(r"lastz-(\d+\.\d+\.\d+)\.tar\.gz", x).group(1).split('.')))
	lastz_versions.reverse()
	if interactive:
		input_is_accepted = False
		while input_is_accepted == False:
			prompt_header = "Multiple versions of lastz are available. Enter the number corresponding to the version you want to download..."
			prompt_versions = ["   %d: %s" % (i + 1, lastz_versions[i]) for i in range(0, len(lastz_versions))]
			if recommended_version in lastz_versions:
				prompt_versions[lastz_versions.index(recommended_version)] += " (recommended)"
			prompt_lines = [prompt_header] + prompt_versions
			prompt = '\n'.join(prompt_lines)
			user_input = raw_input(prompt + '\n')
			try: 
				user_selection = int(user_input)
			except ValueError:
				print("Invalid selection. Try again..")
				continue
			else:
				input_is_accepted = True
			version_to_download = lastz_versions[user_selection - 1]
	else:
		if recommended_version not in lastz_versions:
			raise RuntimeError('Could not locate lastz version "%s" at "%s". You can try the interactive installation option to see if other versions are available.' % (recommended_version, site_url))
		if lastz_versions[0] != recommended_version:
			print('NOTE: the recommended version to be installed "%s" is not the newest version. "%s" appears to be the newest.' % (recommended_version, lastz_versions[0]))
		version_to_download = recommended_version
	if file_name == None:
		file_name = version_to_download
	if version_to_download in old_lastz_versions:
		version_to_download_url = url_path_join(old_site_url, version_to_download)
	else:
		version_to_download_url = url_path_join(dev_site_url, version_to_download)
	output_path = os.path.join(install_path, file_name)
	print('Downloading "%s"...' % version_to_download_url)
	download_handle = urllib2.urlopen(version_to_download_url)
	with open(output_path, 'wb') as output_handle:
		output_handle.write(download_handle.read())
	download_handle.close()
	return output_path

def install_lastz(install_path, executable_path=None, interactive=True,):
	if executable_path == None:
		executable_path = install_path
	#Download 
	lastz_archive_path = download_lastz(install_path, interactive=interactive)
	#Untar 
	tar_handle = tarfile.open(lastz_archive_path, 'r')
	tar_handle.extractall(install_path)
	tar_handle.close()
	#Get path to scr directory in archive
	version = re.match(r"lastz-(\d+\.\d+\.\d+)\.tar\.gz", os.path.basename(lastz_archive_path)).group(1)
	scr_path = os.path.join(install_path, "lastz-distrib-%s" % version, "src")
	#install
	print('Attempting to install lastz...')
	runtime_output_path = os.path.join(install_path, "lastz_compilation_runtime_output.txt")
	with open(runtime_output_path, 'w') as runtime_output_handle:
		os.environ['LASTZ_INSTALL'] = executable_path
		os.chdir(scr_path)
		subprocess.call(["make"], stdout = runtime_output_handle, stderr = subprocess.STDOUT)
		subprocess.call(["make", "install"], stdout = runtime_output_handle, stderr = subprocess.STDOUT)
		test_output = subprocess.check_output(["make", "test"], stderr = subprocess.STDOUT)
		if test_output == "" and "lastz" in os.listdir(executable_path) and "lastz_D" in os.listdir(executable_path):
			print('Installation of lastz %s completed and verified. Executables are in "%s".' % (version, executable_path))
		else:
			print('Error detected during installation. Lastz might not have installed correctly')
	
def install_yasra(install_path, executable_path=None, interactive=True):
	if executable_path == None:
		executable_path = install_path
	#Download 
	yasra_archive_path = download_yasra(install_path, interactive=interactive)
	#Untar 
	tar_handle = tarfile.open(yasra_archive_path, 'r')
	tar_handle.extractall(install_path)
	tar_handle.close()
	#Get path to scr directory in archive
	version = re.match(r"YASRA-(\d+\.\d+)\.tar\.gz", os.path.basename(yasra_archive_path)).group(1)
	scr_path = os.path.join(install_path, "YASRA-%s" % version)
	#install
	print('Attempting to install YASRA...')
	runtime_output_path = os.path.join(install_path, "yasra_compilation_runtime_output.txt")
	with open(runtime_output_path, 'w') as runtime_output_handle:
		os.chdir(scr_path)
		subprocess.call(["./configure", "--prefix=%s" %	 install_path, "--bindir=%s" % executable_path], stdout = runtime_output_handle, stderr = subprocess.STDOUT)
		subprocess.call(["make"], stdout = runtime_output_handle, stderr = subprocess.STDOUT)
		subprocess.call(["make", "install"], stdout = runtime_output_handle, stderr = subprocess.STDOUT)
		if "genomewalker" in os.listdir(executable_path):
			print('Installation of yasra %s completed. Executables are in "%s".' % (version, executable_path))
		else:
			print('Missing files detected. yasra might not have installed correctly')


def get_mummer_versions(site_url):
	url_pattern = "http://sourceforge.net/projects/mummer/files/mummer/%s/MUMmer%s.tar.gz/download"
	links = get_links(site_url)
	link_matches = [re.match(r"/projects/mummer/files/mummer/(\d+\.\d+)/", x) for x in links]
	mummer_versions = list(set([m.group(1) for m in link_matches if m]))
	mummer_files = [url_pattern % (v,v) for v in mummer_versions]
	return (mummer_files, mummer_versions)

def download_mummer(install_path, file_name=None, interactive=True, recommended_version="3.23"):
	version = "3.23"
	url_patern = r"http://sourceforge.net/projects/mummer/files/mummer/\d+\.\d+/(\d+\.\d+)\.tar\.gz/download"
	site_url = "http://sourceforge.net/projects/mummer/files/mummer/"
	mummer_files, mummer_versions = get_mummer_versions(site_url)
	mummer_files = sorted(mummer_files, key=lambda x: map(int, mummer_versions[mummer_files.index(x)].split('.')))
	mummer_files.reverse()
	mummer_versions.sort(key=lambda x: map(int, x.split('.')))
	mummer_versions.reverse()
	if interactive:
		input_is_accepted = False
		while input_is_accepted == False:
			prompt_header = "Multiple versions of MUMmer are available. Enter the number corresponding to the version you want to download..."
			prompt_versions = ["   %d: %s" % (i + 1, mummer_files[i].split('/')[-2]) for i in range(0, len(mummer_versions))]
			if recommended_version in mummer_versions:
				prompt_versions[mummer_versions.index(recommended_version)] += " (recommended)"
			prompt_lines = [prompt_header] + prompt_versions
			prompt = '\n'.join(prompt_lines)
			user_input = raw_input(prompt + '\n')
			try: 
				user_selection = int(user_input)
			except ValueError:
				print("Invalid selection. Try again..")
				continue
			else:
				input_is_accepted = True
			version_to_download = mummer_versions[user_selection - 1]
			file_to_download = mummer_files[user_selection - 1]
	else:
		if recommended_version not in mummer_versions:
			raise RuntimeError('Could not locate MUMmer version "%s" at "%s". You can try the interactive installation option to see if other versions are available.' % (recommended_version, site_url))
		if mummer_versions[0] != recommended_version:
			print('NOTE: the recommended version to be installed "%s" is not the newest version. "%s" appears to be the newest.' % (recommended_version, mummer_versions[0]))
		version_to_download = recommended_version
		file_to_download = mummer_files[mummer_versions.index(recommended_version)]
	if file_name == None:
		file_name = "MUMmer%s.tar.gz" % version_to_download
	output_path = os.path.join(install_path, file_name)
	print('Downloading "%s"...' % file_to_download)
	download_handle = urllib2.urlopen(file_to_download)
	with open(output_path, 'wb') as output_handle:
		output_handle.write(download_handle.read())
	download_handle.close()
	return output_path

def install_mummer(install_path, executable_path=None, interactive=True):
	if executable_path == None:
		executable_path = install_path
	#Download 
	archive_path = download_mummer(install_path, interactive=interactive)
	#Untar 
	tar_handle = tarfile.open(archive_path, 'r')
	tar_handle.extractall(install_path)
	tar_handle.close()
	#Get path to scr directory in archive
	version = re.match(r"MUMmer(\d+\.\d+)\.tar\.gz", os.path.basename(archive_path)).group(1)
	scr_path = os.path.join(install_path, "MUMmer%s" % version)
	#install
	print('Attempting to install MUMmer...')
	runtime_output_path = os.path.join(install_path, "mummer_compilation_runtime_output.txt")
	with open(runtime_output_path, 'w') as runtime_output_handle:
		os.chdir(scr_path)
		subprocess.call(["make", "check"], stdout = runtime_output_handle, stderr = subprocess.STDOUT)
		subprocess.call(["make", "install"], stdout = runtime_output_handle, stderr = subprocess.STDOUT)
	#Check nucmer installation
	nucmer_path = os.path.join(scr_path, "nucmer")
	error_message = "Error in MUMmer installation. nucmer cannot be executed. Try manually installing MUMmer and supply to the path to the installation."
	try:
		nucmer_output = subprocess.check_output([nucmer_path, "-v"], stderr = subprocess.STDOUT)
	except subprocess.CalledProcessError:
		print(error_message)
	else:
		if nucmer_output.split('\n')[1] == '  USAGE: nucmer  [options]  <Reference>  <Query>':
			print('Installation of MUMmer %s completed and verified. Executables are in "%s".' % (version, executable_path))
		else:
			print(error_message)


#Change log
change_log = [('1.0.0',		'First version of the script'),\
				('1.1.0'	'Rewrote. Downloads and installes prerequisites')]
version = change_log[-1][0]

#Constants
program_description = "%s\nVersion: %s" % (__doc__, version)
accepted_lastz_versions = ['1.3.2', '1.03.02']
accepted_readtools_versions = ['1.0.0']
accepted_makeconesnsus_versions = ['1.1.1']
accepted_runyasra_versions = ['2.2.3']
accepted_nucmer_versions = ['3.1']
installer_folder = os.path.abspath(os.getcwd())

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
command_line_parser.add_argument('-o', '--overwrite', default=False, action="store_true",\
								help='Overwrite previous installation in same location.')
if len(sys.argv) == 1:
	command_line_parser.print_help()
	sys.exit(0)
arguments = command_line_parser.parse_args()
arguments.install_path = os.path.join(arguments.install_path, "alignreads")
if arguments.executable_path is None: 
	arguments.executable_path = os.path.join(arguments.install_path, 'bin')


#Make installation directory
if os.path.exists(arguments.install_path):
	if arguments.overwrite:
		shutil.rmtree(arguments.install_path)
	else:
		logging.fatal("Installation directory exists. Use the --overwrite option to remove previous installation.")
os.mkdir(arguments.install_path)
if arguments.install_path != arguments.executable_path:
	os.mkdir(arguments.executable_path)


#Unpack Installation
tar_handle = tarfile.open(os.path.join(installer_folder, 'uninstalled_content.tar'), 'r')
tar_handle.extractall(installer_folder)
tar_handle.close()

#Move files to installation directory
unpacked_uninstalled_content = os.path.join(installer_folder, 'uninstalled_content')
for name in os.listdir(unpacked_uninstalled_content):
	os.rename(os.path.join(unpacked_uninstalled_content, name), os.path.join(arguments.install_path, name))
os.rmdir(unpacked_uninstalled_content)

#Validation and installation of requirements
if arguments.python is None:
	arguments.python = subprocess.check_output(['which', 'python'], stderr = subprocess.STDOUT).strip()
	python_version = sys.version.split(' ')[0]
	if arguments.python is None:
		raise TypeError('Cannot locate python. Use option -l/--python-location')
	else:
		print "Found python %s at %s" % (python_version, arguments.python)

if arguments.lastz is False:
	install_lastz(arguments.install_path, executable_path=arguments.executable_path, interactive=arguments.interactive)
	arguments.lastz = os.path.join(arguments.executable_path, 'lastz')
elif arguments.lastz is None:
	arguments.lastz, lastz_version = find_active_version('lastz')
	if arguments.lastz is None:
		raise TypeError('Cannot locate lastz. Specifcy location using option --lastz or omit option to download and install automatically.')
	else:
		print "Found lastz %s at %s" % (lastz_version, arguments.lastz)
generic_program_validation(arguments.lastz, accepted_lastz_versions)

if arguments.yasra is False:
	install_yasra(arguments.install_path, executable_path=arguments.executable_path, interactive=arguments.interactive)
	arguments.yasra = arguments.executable_path

if arguments.nucmer is False:
	install_mummer(arguments.install_path, executable_path=arguments.executable_path, interactive=arguments.interactive)
	arguments.nucmer = os.path.join(arguments.executable_path, 'nucmer')
elif arguments.nucmer is None:
	arguments.nucmer, nucmer_version = find_active_version('nucmer')
	if arguments.nucmer is None:
		raise TypeError('Cannot locate nucmer. Specifcy location using option --nucmer.')
	else:
		print "Found nucmer %s at %s" % (nucmer_version, arguments.nucmer)
generic_program_validation(arguments.nucmer, accepted_nucmer_versions)

#Modify Default Configuration File
print(arguments)
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
shell_text = '#!/bin/csh\n%s %s $*\n' % (arguments.python, alignreads_location)
with open(shell_script_location, 'w') as shell_handle:
	shell_handle.write(shell_text)
subprocess.call(['chmod', '+x', shell_script_location], stdout = subprocess.PIPE, stderr = subprocess.STDOUT)

print 'The installation has completed successfully.'


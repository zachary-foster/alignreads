#!/usr/bin/env python

import os
import sys
import argparse
import urllib2
import re
import subprocess
import tarfile
from urlparse import urlsplit, urlunsplit

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

def main(arguments):
	print install_mummer("/nfs/Grunwald_Lab/Foster/test")
	
if __name__ == '__main__':
	sys.exit(main(sys.argv[1:]))

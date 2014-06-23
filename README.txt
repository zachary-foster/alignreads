Installation Instructions:

1) Put the alignreads folder (perhaps compressed) in desired installation
location. Once installed, it should not be moved.
2) Uncompress the folder if necessary using:
	"tar -xvf alignreads_v#-#-#.tar"
3) Change directories so that you are in the alignreads folder. 
4) Compile the install script, giving it the path to YASRA:
	"python install.py /path/to/YASRA"
If specific external dependencies are not found automatically, then
they will need to be found/installed and specified through the options
of install.py. In order to have alignreads be in the shell search path, you 
should use the -i/--shell-init-file option of install.py to modify your 
shell startup preferences.

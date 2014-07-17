Installation Instructions:

1) Download the alignreads_#-#-#.tar.gz file and put on server.
2) Uncompress the folder using:
	"tar -xvzf alignreads_#-#-#.tar.gz"
3) Change directories so that you are in the alignreads folder. 
4) Run the installation script:
	"python install.py /path/to/install/location"
The install script has many options to adapt to different situations.
It will attempt to download and install all prerequisites (except biopython). 
Using command line options to install.py, you can tell it where an already 
installed prerequisite exists or have it look for it in your $PATH.
If the automated installation fails (typically due to non-standard system 
configurations), you might have to install the prerequisite yourself. 

NOTE: Alignreads requires Biopython for parsing of YASRA output. 
If you do not already have Biopython installed, you should install it or 
the Anaconda environment, which includes Biopython. 

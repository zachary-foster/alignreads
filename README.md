# Alignreads

Alignreads is a wrapper for YASRA (http://www.bx.psu.edu/miller_lab/). 
The principal function of alignreads is to facilitate easy execution of 
YASRA and to parse its output. 

YASRA is a reference guided assembler that has the ability to extend 
the edges of alignments de novo interactively. The minimum inputs are a 
reference sequence and reads to be aligned, but there are many options. 
Use `alignreads -h` after installation to see a full list of options. 

Alignreads has the following dependencies:

* YASRA
* lastz (used by YASRA)
* nucmer (from the MUMmer tool kit) 
* Biopython (used to parse YASRA's output)

The installer of alignreads can typically download and install most of 
these automatically. See INSTALL.txt for details.

YASRA was created by Aakrosh Ratan at Pennsylvania State University in 
the Miller lab. 

Alignreads was created by Zachary Foster at Oregon State University in 
the Liston lab. 

## Installation

Alignreads has an installation script that attempts to download and install all dependencies where possible. 
This automatic installation should work on most system configurations with access to the internet and common compiling software (e.g. `gcc`)

In the examples below, replace terms between < and > with values appropriate to your system and needs:

### Downloading alignreads

Alignreads releases are available from Git Hub at https://github.com/zachary-foster/alignreads/releases.
The `wget` Linux command can be used to download a release from the command line:

```
wget https://github.com/zachary-foster/alignreads/releases/<version to install>
```

You can also download the current development version of alignreads using `git`:

```
git clone https://github.com/zachary-foster/alignreads
```

### Unpacking the release 

Use `tar` to unpack the alignreads directory:

```
tar -xvf <version to install>.tar.gz
cd <version to install>.tar.gz
```

### Installer help information

To see what options are available for the installation process, run the installation script without any arguments: 

```
python install.py
```

### Running the interactive installer

By default, the installer allows you to interactively choose which version of dependencies to install and attempts to download and install them:

```
python install.py <path to installation location>
```

The `<path to installation location>` will be the where alignreads will be installed. 
A folder named `alignreads` will be created there.

### Non-interactive installation

Alternatively, to automatically install the recommended versions of dependencies non-interactively, the `-i` / `--not-interactive` option can be used:

```
python install.py -i <path to installation location>
```

### Using currently installed dependecies 

If some of the dependencies are already installed on you system, you can use those versions by including the corresponding installer option (See installer help menu). 
If the already-installed dependencies are in your `PATH` (i.e. you can use them from the command line in any directory), just supply the corresponding option without arguments.
For example, if `lastz` is already installed and in your `PATH`:

```
python install.py --lastz <path to installation location>
```

If a dependency is installed, but not in `PATH`, then give the corresponding option the location to find it:

```
python install.py --lastz <path to lastz> <path to installation location>
```

### Putting alignreads in your shell's search path

The installation of alignreads contains a executable shell script that simply executes alignreads with a specified instance of `python`. 
This shell script allows for alignreads to be run by typing `alignreads` instead of `python alignreads.py`.
It is often convienent to put this executable in your shell's search path, so that typing `alignreads` runs the program regardless of current working directory.

How this is done depends on what shell you are using. 
To find out what shell you are using, paste the following command into your terminal:

```
ps -p $$ -o cmd=
```

#### For Bash/Sh/Ksh

In your home directory, there should be a `.bashrc` or `.profile` file depending on your system.
This file contains a list of bash commands that are run each time `bash` is run (i.e. a terminal is opened).
To put alignreads in your search path permanently, add something like the following line to the end of that file. 

```
export PATH="$PATH:<path to installation>"
```

Here is an example of the line I would add to `.bashrc` if I installed alignreads in `/home/fosterz` on my system.

```
export PATH="$PATH:/home/fosterz/alignreads"
```


#### For Csh/Tcsh

In your home directory, there should be a `.cshrc` or `.login` file, depending on your system.
This file contains a list of csh commands that are run each time `csh` is run.
To put alignreads in your search path permanently, add something like the following line to the end of that file. 

```
setenv PATH $PATH:<path to installation>
```

Here is an example of the line I would add to `.cshrc` if I installed alignreads in `/home/fosterz` on my system.

```
setenv PATH $PATH:/home/fosterz/alignreads
```


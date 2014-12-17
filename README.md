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
It is often convenient to put this executable in your shell's search path, so that typing `alignreads` runs the program regardless of current working directory.

How this is done depends on what shell you are using. 
To find out what shell you are using, paste the following command into your terminal:

```
ps -p $$ -o cmd=
```

**For Bash/Sh/Ksh:**

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


**For Csh/Tcsh:**

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

## Running alignreads

Alignreads has an intimidating amount of arguments because it gives access to the arguments of its constituent programs.
However, most of these arguments are rarely used.
Running alignreads without arguments will print a help menu with all the options and their default values.

The simplest alignreads command possible uses default values for all of the options. 
For example, to assemble reads in a fasta file named `read.fa` using a reference in a file called `reference.fa`, assuming both files are in the current working directory and alignreads is in your shell's search path, type:

```
alignreads reads.fa reference.fa
```

In most cases, at least some options should be used.
Examples and explanations of commonly needed options follow.

### General alignreads options

**-y / --output-directory**

Specify the location of the output directory. 
By default, alignreads creates an output directory for each run in the current working directory.

For example, to create the output directory in the folder `~/my_assemblies` regardless of current working directory:

```
alignreads reads.fa reference.fa --output-directory ~/my_assemblies
```

**-c / --config-file** 

Alignreads uses a configuration file to specify the default values of all options. 
The configuration file is simply a python script that defines variables. 
The default configuration file is located in the installed alignreads folder and is called `default_configuration.py`. 
You can make copies of this file and change the values to specify your own defaults for different tasks.

For example, to use a configuration file called `bacterial_configuration.py` that specifies the default option values for assembling bacterial genomes:

```
alignreads reads.fa reference.fa --config-file bacterial_configuration.py
```

Any other options used on the command line will override the defaults in the configuration file if used together.

For example, say you are only assembling a specific part of a bacterial genome (i.e. not circular). You could run:

```
alignreads reads.fa reference.fa --config-file bacterial_configuration.py -o linear
```

### Contig assembly options

**-a / --single-step**

YASRA uses an iterative process to improve assemblies.
If additional iterations after the first do not improve the assembly YASRA throws an error. 
If this happens, you have to use the `-a` / `--single-step` option to prevent the error. 
A future goal is to circumvent this inconvenient behavior. 

For example:

```
alignreads reads.fa reference.fa --single-step
```

**-t / --read-type**

The type of reads, either `454` or `solexa`. 
* `454`: longer, less accurate Roche 454 pyrosequencer reads. 
* `solexa`: shorter, more accurate Illumina reads. 

For example, if the reads being used were produced by an Illumina HiSeq:

```
alignreads reads.fa reference.fa -t solexa
```

**-o / --read-orientation**

Whether the thing being assembled is a `linear` or `circular` DNA molecule.

For example, if a chromosome is being assembled:

```
alignreads reads.fa reference.fa -o linear
```

**-p / --percent-identity**

How similar the reference is to the sequence being assembled. 
The interpretation of this option is effected by `--read-type`.
Possible values are listed below.

For 454:

* `same`       : about 98% identity between target & reference
* `high`       : about 95% identity between target & reference
* `medium      : about 90% identity between target & reference
* `low`        : about 85% identity between target & reference
* `verylow`    : about 75% identity between target & reference
* `desperate`  : really low identity (rather slow)

For Solexa/Illumina:

* `same`        : about 95% identity between target & reference
* `medium`      : about 85% identity between target & reference
* `desperate`   : low scores (rather slow)

For example, to assemble Illumina reads with a closely related reference:

```
alignreads reads.fa reference.fa -t solexa -p same
```


### Contig alignment options 

The program `nucmer` from the MUMmer tool kit is used to align contigs produced by YASRA to the reference. 
`nucmer` has many options that control this process. 
To fully understand the effects of the options, a understanding of how `nucmer` works is needed.
I recommend looking over the `nucmer` documentation (http://mummer.sourceforge.net/manual/#nucmer). 


### Consensus generation options 

Alignreads makes a consensus of all of the aligned contigs.
There are a few options that are almost essential for this process to work correctly. 
All of the following options accept a range of numbers in the format  `<min>-<max>` (e.g. `5-10`), inclusive.
The <min> or the <max> can be left out to indicate no minimum/maximum limit (e.g. `5-` means "at least five").
Multiple ranges can be specified if separated by commas (e.g. `1-3,100-` means "one to three or over 100").

**-g / --quality-read-filter**

The acceptable quality scores for reads.
Reads outside this range will not be included in the consensus sequences.

**-m / --depth-position-masking**

The range(s) of acceptable read depth.
Positions outside this range will be masked in the consensus sequences.

For example, to mask all positions with less than 10 read depth in the consensus sequence:

```
alignreads reads.fa reference.fa -m 10-
```

**-b / --proportion-base-filter**

The acceptable range(s) for the proportion of bases at a given position that support a given call.
Nucleotides with proportions outside of this range will be ignored when condensing the position to an IUPAC character in the consensus.

For example, to ignore all SNPs that have a less than 10% frequency:

```
alignreads reads.fa reference.fa -b 0.1-
```

**-d / --depth-position-filter**

Set the depth range(s) for position filtering.
Positions outside this range will not be included in the consensus sequences.

For example, to remove indels that occur less than 5% of the time:

```
alignreads reads.fa reference.fa -d 0.05-
```


### Making multiple consensus sequences per assembly

Running YASRA can take a long time whereas aligning the contigs and making a consensus sequence is relativly quick.
This means that alot of time can be wasted optimizing contig alignment and consensus generation parameters if a new assembly is done each try.
Therefore, it is possible to redo everything downstream of the assembly step with different options by supplying `alignreads` with the path to a previously-generated output directory instead of the read and reference file. 
A new sub-directory will be created within the old output directory for each new run. 

For example, to make a new consensus from a previous assembly stored in alignreads output directory named `454.fa_rhino_template.fa_Wed-Dec-17-15:36:23-2014`:

```
alignreads 454.fa_rhino_template.fa_Wed-Dec-17-15:36:23-2014 -d 0.15-
```
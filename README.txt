Alignreads is a wrapper for YASRA (http://www.bx.psu.edu/miller_lab/). 
The principal function of alignreads is to facilitate easy execution of 
YASRA and to parse its output. 

YASRA is a reference guided assembler that has the ability to extend 
the edges of alignments de novo iteratively. The minimum inputs are a 
reference sequence and reads to be aligned, but there are many options. 
Use `alignreads -h` after installation to see a full list of options. 

Alginreads has the following dependencies:
	>YASRA
	>lastz (used by YASRA)
	>nucmer (from the MUMmer tool kit) 
	>Biopython (used to parse YASRA's output)

The installer of alignreads can typically download and install most of 
these automatically. See INSTALL.txt for details.

YASRA was created by Aakrosh Ratan at Pennsylvania State University in 
the Miller lab. 

Aligreads was created by Zachary Foster at Oregon State Univeristy in 
the Liston lab. 


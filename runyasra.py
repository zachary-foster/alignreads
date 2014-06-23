#!/usr/bin/env python

###Imports and Import Validation###################################################################################################################
import os, sys, copy, string, re, logging
from datetime import *
from optparse import *
from subprocess import *


accepted_readtools_versions = ['1.0.0']
try:
    import readtools
except:
    raise ImportError("Can not import readtools.py. Make sure that readtools.py is located in the python search path.")
else:
    if readtools.program_version not in accepted_readtools_versions:
        raise ImportError("Wrong version of readtools.py detected. Version found: '%s\nCompatible Versions: %s" % (readtools.program_version, ", ".join(accepted_readtools_version)))
######################################################################################################################################################

###Variable Initialization############################################################################################################################
timeStamp = datetime.now().ctime().replace(' ','-')  #Ex: 'Mon-Jun-14-11:08:55-2010'
commandLine = copy.deepcopy(sys.argv)
defaultYasraPath = '/smokey/bin/YASRA'
defaultLastzPath = 'lastz'
cwd = os.getcwd()
program_name, program_version, progArgNum = ('runyasra','2.2.3', 2)
progUsage = 'python %s <Reads> <Reference> [options]' % program_name
accepted_lastz_versions = ['1.03.03']
######################################################################################################################################################

###Command Line Parser################################################################################################################################
if '--touch' not in commandLine:
    try:
        cmndLineParser  = OptionParser(usage=progUsage, version="Version %s" % program_version)
        cmndLineParser.add_option('-t', '--read-type',          action='store',         default='solexa',   type='choice',  choices=['solexa','454'],\
                                  help="Specify the type of reads. (Default: solexa)")
        cmndLineParser.add_option('-o', '--orientation',        action='store',         default='circular', type='choice',  choices=['circular','linear'],\
                                  help="Specify orientation of the sequence. (Default: circular")
        cmndLineParser.add_option('-p', '--percent-identity',   action='store',         default='same',     type='choice',  choices=['same','high','medium','low','verylow','desperate'],\
                                  help="The percent identity (PID in yasra). The settings correspond to different percent values depending on the read type (-t). (Defalt: same)")
        cmndLineParser.add_option('-n', '--contig-overlap',     action='store',         default=10,     type='int',\
                                  help="The number of bases that must align (either match or mismatch) between contigs to be merged. (Defalt: 10)")
        cmndLineParser.add_option('-i', '--overlap-percent-identity',     action='store',         default=95,     type='float',\
                                  help="Percent identity in the aligned region (match * 100.0 / (match + mismatch)) between contigs to be merged. (Defalt: 95)")
        cmndLineParser.add_option('-c', '--overlap-continuity',     action='store',         default=95,     type='float',\
                                  help="Continuity ((match + mismatch) * 100.0 / (match + mismatch + gaps)) between contigs to be merged. (Defalt: 95)")
        cmndLineParser.add_option('-m', '--makefile-path',      action='store',         default=None,       type='string',  metavar='PATH',\
                                  help="Specify path to external makefile used by YASRA. (Default: use the makefile built in to runyasra)")
        cmndLineParser.add_option('-b', '--yasra-binary-path',  action='store',         default=None,       type='string',  metavar='PATH',\
                                  help="Specify the path YASRA's folder. (Default: %s)" % defaultYasraPath)
        cmndLineParser.add_option('-z', '--lastz-binary-path',  action='store',         default='',       type='string',  metavar='PATH',\
                                  help="Specify the path to lastz. (Default: lastz)")
        cmndLineParser.add_option('-s', '--single-step',        action='store_true',    default=False,\
                                  help="Activate yasra's single_step option (Default: run yasra normally)")
        cmndLineParser.add_option('-v', '--verbose',            action='store_true',    default=False,\
                                  help='Print relevant statistics and progresss reports. (Default: run silently)')
        cmndLineParser.add_option('-r', '--remove-dots-reads',  action='store_true',    default=False,\
                                  help='Replace dots with Ns in the reads file before runnning yasra. The modified file is placed in the output filder.(Default: create a link to the original file)')
        cmndLineParser.add_option('-f', '--remove-dots-ref',    action='store_true',    default=False,\
                                  help='Replace dots with Ns in the reference file before runnning yasra. The modified file is placed in the output filder.(Default: create a link to the original file)')
        cmndLineParser.add_option('-d', '--dos2unix-ref',       action='store_true',    default=False,\
                                  help='Run dos2unix on the reference file before yasra. The modified file is placed in the output filder. (Default: create a link to the priginal reference)')
        cmndLineParser.add_option(      '--touch',       action='store_true',    default=False,\
                                  help='Load silently and do nothing.')
        cmndLineParser.add_option("-y", "--output-directory", action="store", default=os.getcwd(), type="string", metavar="PATH",\
                               help="Specify where the output directory will be made. (Default: current working directory)")
        (options, args) = cmndLineParser.parse_args(commandLine)
        if len(args) == 1:
            cmndLineParser.print_help()
            sys.exit(0)
        if len(args) - 1 != progArgNum:
            raise TypeError('%s takes exactly %d argument(s); %d supplied' % (program_name, progArgNum, len(args) - 1), 0)
        if options.yasra_binary_path is None:
            options.yasra_binary_path = defaultYasraPath
        readsPath = os.path.join(cwd, args[-2])
        refPath = os.path.join(cwd, args[-1])
        if os.path.exists(readsPath) == False:
            raise TypeError('Invalid path to the reads file: %s' % readsPath,0)
        if os.path.exists(refPath) == False:
            raise TypeError('Invalid path to the reference file: %s' % refPath,0)
        outDirName = '%s_%s_%s' % (os.path.basename(readsPath), os.path.basename(refPath), timeStamp)
        outDirPath = os.path.join(os.getcwd(),outDirName)   #output directory is located in the current working directory
    except SystemExit:
        raise
    except:
        print "An error occured during command line parseing:\n%s" % sys.exc_info()[0]
        raise
    ######################################################################################################################################################

    ###Input Data Vaildation##############################################################################################################################
    def validateFastaForYasra(path):
        with open(path, 'r') as handle:
            count = 0
            for line in handle.readlines():
                if line[0] == '>':
                    if line[1] == '@':
                        raise readtools.InputValidationError('The file at "%s" has reads that begin with the character "@" on line %d. This causes the output SAM file from YASRA to have incorrect syntax. Remove the "@" from the start of the specifed file and try again.' % (path, count))
                elif '.' in line:
                    raise readtools.InputValidationError('The file at "%s" has reads contain the character "." in their sequence on line %d. This is equivalnt to a "N" in the IUPAC convention, but is not recgnoized by YASRA. Replace every "." with "N" in the specifed file and try again.' % (path, count))
                count += 1
    try:
        validateFastaForYasra(readsPath)
        validateFastaForYasra(refPath)
    except readtools.InputValidationError as error:
        error.outputDirectory = outDirPath
        raise
    except:
        print "An error occured during validation of input files:\n%s" % sys.exc_info()[0]
        raise
    ######################################################################################################################################################

    ###Initialize output directory########################################################################################################################
    try:
        os.mkdir(outDirPath)   #create output directory
        os.chdir(outDirPath)   #move into the output directory
    except:
        print "An error occured during output directory creation:\n%s" % sys.exc_info()[0]
        raise

    try:
        newReadsPath = os.path.join(outDirPath, os.path.basename(readsPath))
        newRefPath = os.path.join(outDirPath, os.path.basename(refPath))
        os.symlink(readsPath, newReadsPath)
        os.symlink(refPath, newRefPath)
    except:
        print "An error occured during creation of symbolic links to input file:\n%s" % sys.exc_info()[0]
        raise
    ######################################################################################################################################################

    ###Makefile Creation##################################################################################################################################
    try:
        if options.makefile_path is None:
            logging.debug('Creating the YASRA makefile...')
            makefileData = '''\
#for a full scale assisted assembly:
#  keep a FASTA/FASTQ file with the reads from the target genome,
#  keep a FASTA file with the reference genome sequence,
#  change the values of the variable C,READS,REFERENCE and then type:
#
#  make TYPE= ORIENT= PID= &> Summary
#  
#  The choices for TYPE are '454' and 'solexa'. '454' refers to reads from 454
#  technology which are more than 100 bp long. 'solexa' refers to shorter reads
#  in base-space from Illumina or SOLiD.
#	
#  The choices for ORIENT are 'linear' and 'circular'. It refers to the 
#  orientation of the reference genome. (example: mtDNA would be circular)
#
# The choices for PID are:
# 
# --for 454 reads:
#    'same'       : about 98% identity
#    'high'       : about 95% identity
#    'medium      : about 90% identity
#    'low'        : about 85% identity
#    'verylow'    : about 75% identity
#    'desperate'  : realy low identity (rather slow)
#
# --for solexa reads:
#	'same'        : about 95% identity
#	'medium'      : about 85% identity
#	'desperate'   : low scores (rather slow)
#
# The module "best_hit" selects one alignment for each read. The user can select
# one of the following options:
#
# -u : Ignore reads with multiple alignments. This is the default behavior in
#      this Makefile.
# -s : Choose the place with the highest number of matches. If two alignments 
#      have equal number of matches, then choose one of them randomly.
# -b : Choose the best alignment only if it has x% (x can be user-specified, e.g
#      -b 3 for x=3) more matches than the second best hit. (We use x=3 and use
#      this option internally for whole genome analyses).
#
# The recursive  mode of assembly is rather slow because we try to walk through
# the small gaps and close the contigs. However, if we want to ignore the gaps 
# and want quicker results (and this is the mode I would advise most of the 
# time) is by typing:
#
#  make single_step TYPE= ORIENT= PID= &> Summary
#
# Final output of the process are the following files:
#   Final_Assembly : a FASTA file with the consensus sequence
#   alignments.sam : a SAM file with the alignments. This can be converted to a
#                    BAM file and view with a multitude of viewers
#   contigs.ace    : a  ACE file with the alignments for viewing with Hawkeye
#
# The file alignments.sam replaces "Assembly.qual" in the previous versions of
# YASRA. alignments.sam can be used to get all the information present in
# Assembly.qual by use of SAMtools (http://samtools.sourceforge.net/).
#
# For more information regarding options and tools in YASRA please contact :
# 
# ratan@bx.psu.edu
#
C=''' + options.yasra_binary_path + '''

# the fasta file with the reads
READS=''' + os.path.basename(readsPath) + '''

# the fasta file with the reference sequence
TEMPLATE=''' + os.path.basename(refPath) + '''

# the orientation of the reference sequence
ORIENT=''' + options.orientation + '''

# the type of input sequence 454/solexa
TYPE=''' + options.read_type + '''

# the expected percent identity between the reference and target genomes
PID=''' + options.percent_identity + '''

ifeq ($(TYPE), 454)
''' +'\t'+ '''MAKE_TEMPLATE=min=150
''' +'\t'+ '''ifeq ($(PID),same)
''' +'\t\t'+ '''Q=--yasra98
''' +'\t'+ '''endif
''' +'\t'+ '''ifeq ($(PID),high)
''' +'\t\t'+ '''Q=--yasra95
''' +'\t'+ '''endif
''' +'\t'+ '''ifeq ($(PID),medium)
''' +'\t\t'+ '''Q=--yasra90
''' +'\t'+ '''endif
''' +'\t'+ '''ifeq ($(PID), low)
''' +'\t\t'+ '''Q=--yasra85
''' +'\t'+ '''endif
''' +'\t'+ '''ifeq ($(PID), verylow)
''' +'\t\t'+ '''Q=--yasra75
''' +'\t'+ '''endif
''' +'\t'+ '''ifeq ($(PID), desperate)
''' +'\t\t'+ '''Q=Y=2000 K=2200 L=3000
''' +'\t'+ '''endif
''' +'\t'+ '''R=--yasra98
''' +'\t'+ '''names=darkspace
endif

ifeq ($(TYPE), solexa)
''' +'\t'+ '''MAKE_TEMPLATE=N=100 min=30
''' +'\t'+ '''SOLEXA=-solexa
''' +'\t'+ '''ifeq ($(PID),same)
''' +'\t\t'+ '''Q=--yasra95short
''' +'\t'+ '''endif
''' +'\t'+ '''ifeq ($(PID),medium)
''' +'\t\t'+ '''Q=--yasra85short
''' +'\t'+ '''endif
''' +'\t'+ '''ifeq ($(PID), desperate)
''' +'\t\t'+ '''Q=T=0 W=7 K=1200 L=1400
''' +'\t'+ '''endif
''' +'\t'+ '''R=--yasra95short
''' +'\t'+ '''names=full
endif

ifeq ($(ORIENT), circular)
''' +'\t'+ '''CIRCULAR=--circular
endif

all:step1 step2 step3 step4 step5

step1:
''' +'\t'+ '''# Assemble on the original template
''' +'\t'+ '''make assemble_hits T=$(TEMPLATE) P="$Q" V=70 N=1

step2:
''' +'\t'+ '''$C/genomewalker Assembly1 hits_$(TEMPLATE) $(TEMPLATE)
''' +'\t'+ '''@rm Assembly* hits* template[0-9]* 

step3:
''' +'\t'+ '''# find if there are reads that align without the coverage option
''' +'\t'+ options.lastz_binary_path + ''' template[multi] $(READS)[nameparse=${names}] $R \\
''' +'\t\t'+ '''--coverage=70 --ambiguous=iupac \\
''' +'\t\t'+ '''--format=general:name1,zstart1,end1,text1,name2,strand2,zstart2,end2,text2,nucs2 |\\
''' +'\t'+ '''$C/best_hit -u |\
''' +'\t'+ '''sort -k 1,1 -k 2,2n -k 3,3n > hits_template
''' +'\t'+ options.lastz_binary_path + ''' template[multi] $(READS)[nameparse=${names}] --yasra85short \\
''' +'\t\t'+ '''--coverage=50 --ambiguous=iupac \\
''' +'\t\t'+ '''--format=general:name1,zstart1,end1,text1,name2,strand2,zstart2,end2,text2,nucs2 |\\
''' +'\t'+ '''$C/best_hit -u |\\
''' +'\t'+ '''sort -k 1,1 -k 2,2n -k 3,3n > rejects_template

step4:
''' +'\t'+ '''$C/trim_assembly template hits_template rejects_template > AssemblyX
''' +'\t'+ '''$C/make_template AssemblyX noends $(MAKE_TEMPLATE) > final_template
''' +'\t'+ '''@rm AssemblyX template 
''' +'\t'+ '''@rm hits_template rejects_template
''' +'\t'+ '''
step5:
''' +'\t'+ ''' make final_assembly T=final_template P="$R" V=70
''' +'\t'+ '''@rm final_template 
''' +'\t'+ '''
stepx:
''' +'\t'+ '''$C/make_template Assembly$W $(MAKE_TEMPLATE)> template$X
''' +'\t'+ '''make assemble_hits T=template$X P="$R" V=70 N=$X

assemble_hits:
''' +'\t'+ options.lastz_binary_path + ''' $T[multi] $(READS)[nameparse=${names}] $P \\
''' +'\t\t'+ '''--coverage=$V --ambiguous=iupac \\
''' +'\t\t'+ '''--format=general:name1,zstart1,end1,text1,name2,strand2,zstart2,end2,text2,nucs2 |\\
''' +'\t'+ '''$C/best_hit -u |\\
''' +'\t'+ '''sort -k 1,1 -k 2,2n -k 3,3n > hits_$T
''' +'\t'+ '''$C/assembler -o -c -h hits_$T > Assembly_$N
''' +'\t'+ '''$C/genomewelder $(CIRCULAR) -n ''' + str(options.contig_overlap) + ''' -i ''' + str(options.overlap_percent_identity) + ''' -c ''' + str(options.overlap_continuity) + ''' Assembly_$N > Assembly$N

single_step:
''' +'\t'+ '''make final_assembly T=$(TEMPLATE) P="$Q" V=70

final_assembly:
''' +'\t'+ options.lastz_binary_path + ''' $T[multi] $(READS)[nameparse=${names}] $P \\
''' +'\t\t'+ '''--coverage=$V --ambiguous=iupac \\
''' +'\t\t'+ '''--format=general:name1,zstart1,end1,text1,name2,strand2,zstart2,end2,text2,nucs2 |\\
''' +'\t'+ '''$C/best_hit -u |\\
''' +'\t'+ '''sort -k 1,1 -k 2,2n -k 3,3n |\\
''' +'\t'+ '''$C/assembler -r -o -c \\
''' +'\t\t'+ '''-h /dev/stdin \\
''' +'\t\t'+ '''-s alignments.sam \\
''' +'\t\t'+ '''-a contigs.ace > Final_Assembly

clean:
''' +'\t'+ '''rm Final_Assembly alignments.sam contigs.ace'''
            logging.debug('YASRA makefile created.')
        else:
            makefileHandle = open(options.makefile_path, 'w')
            makefileData = makefileHandle.read()
            makefileHandle.close()
        makefilePath = os.path.join(outDirPath, 'Makefile')
        makefileHandle = open(makefilePath, 'w')
        makefileHandle.write(makefileData)
        makefileHandle.close()
    except:
        print "An unknown error occured during creation of yasra makefile:"
        raise
    ######################################################################################################################################################

    def printProcess(process):
        '''Prints the standard ouput and error messages of a process while the process ia running.'''
        outLen = 0
        errLen = 0
        out = ''
        err = ''
        while process.poll() is None:  #while it hasnt finished...
            (outData, errData) = process.communicate()
            outDiff =  len(outData) - outLen
            errDiff =  len(errData) - errLen
            if outDiff > 0:
                outLen += outDiff
                out += outData[-outDiff:]
                print outData[-outDiff:]
            if errDiff > 0:
                errLen += errDiff
                err += errData[-errDiff:]
                print errData[-errDiff:]
        return (out, err)

    ###Run yasra##########################################################################################################################################
    makeCmndLine = ['make','TYPE=' + options.read_type,'ORIENT=' + options.orientation,'PID=' + options.percent_identity]
    if options.single_step:
        makeCmndLine.insert(1,'single_step')
    makeStdOut = open(os.path.join(outDirPath, 'yasra_standard_output.txt'), 'w')
    makeStdErr = open(os.path.join(outDirPath, 'yasra_standard_error.txt'), 'w')
    makeProcess = Popen(makeCmndLine, stdout=PIPE, stderr=PIPE)
    #if options.verbose:
    #    (outData, errData) = printProcess(makeProcess)
    #else:
    (outData, errData) = printProcess(makeProcess)  
    makeProcess.wait()
    makeStdOut.write(outData)
    makeStdErr.write(errData)
    makeStdOut.close()
    makeStdErr.close()
    if makeProcess.returncode == 0:   #yasra completed normally
        if options.verbose:
            print 'yasra output saved in the directory: %s' % outDirPath
    else:
        raise Exception('yasra returned a non-zero code; it may have not completed succesfully', 0)
    dontChange = ('Makefile',os.path.basename(readsPath), os.path.basename(refPath))
    outPaths = [os.path.join(outDirPath, path) for path in os.listdir(outDirPath) if os.path.isfile(path) and path not in dontChange]
    renamedPaths = [os.path.join(outDirPath, '%s_%s_%s%s' % (os.path.splitext(path)[0], os.path.basename(readsPath), os.path.basename(refPath), os.path.splitext(path)[1])) for path in os.listdir(outDirPath) if os.path.isfile(path) and path not in dontChange]
    for index in range(0,len(outPaths)):
        os.rename(outPaths[index],renamedPaths[index])
    ######################################################################################################################################################

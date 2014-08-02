#!/usr/bin/env python

###Imports and Import Validation###
import readtools
import os, sys, copy
from optparse import *
from datetime import *
import logging

### Logging
# create logger
logger = logging.getLogger('')
####

accepted_readtools_versions = ['1.0.0']
try:
    import readtools
except:
    raise ImportError("Can not import readtools.py. Make sure that readtools.py is located in the python search path.")
else:
    if readtools.program_version not in accepted_readtools_versions:
        raise ImportError("Wrong version of readtools.py detected. Version found: '%s\nCompatible Versions: %s" % (readtools.program_version, ", ".joint(accepted_readtools_version)))

###Variable Initalizations###
argList     = sys.argv #argumen list supplied by user
argNum      = len(argList) #the number of arguments supplied
debugLog    = ['***********DEBUG LOG***********\n'] #where all errors/anomalies are recorded; saved if the -d modifier is supplied
timeStamp = datetime.now().ctime().replace(' ','-').replace(':','-').replace('--','-')  #Ex: 'Mon-Jun-14-11-08-55-2010'
cwd         = os.getcwd()
program_name, program_version, progArgNum = ('makeConsensus.py','1.1.1', 2)
progDescription =\
'''
Makes a consensus sequence for each reference to which reads are aligned to in a SAM file.
'''
progUsage = 'python %s <SAM file> <Reference FASTA file> [options]' % program_name
spacingCharacters = ['-','~']
printLog = []

def errorExit(message=None,exitStatus=1):
    '''Version 1.0
    Is called when the script encounters a fatal error. Prints the debug log to standard out (usually the screen)'''
    if message:
        print '%s: Error: %s' % (program_name, message)
    else:
        print program_name +': Unknown error, printing debug log...'
        for line in debugLog: print line   #print debug log
    sys.exit(exitStatus)
    
def verbose(toPrint):
    print toPrint,
    if options.verbose:
        print toPrint,
        printLog.append(toPrint)

def getIUPAC(baseValues):
    def removeRepeats(aList):
        for entry in aList:
            if aList.count(entry) > 1:
                aList.remove(entry)
                return removeRepeats(aList)
        return aList
    '''Takes a list of base character values (ACTG-~N) and condenses them into a single IUPAC code. Assumes only input characters to be ACTG-~N'''
    def IUPAC(bases):
        conversion = {'CT':'Y','AG':'R','AT':'W','CG':'S','GT':'K','AC':'M','AGT':'D','ACG':'V','ACT':'H','CGT':'B','ACGT':'N'}
        bases.sort()  #['A', 'C', 'G', 'T']
        if bases[0].islower():
            bases = map(str.upper,bases)
            return str.lower(conversion[''.join(bases)])
        else: return conversion[''.join(bases)]
    chars = removeRepeats(list(baseValues))
    chars.sort()  #['-', 'A', 'C', 'G', 'N', 'T', 'a', 'c', 'g', 'n', 't', '~']
    if len(chars) == 0: return '-'
    if len(chars) == 1: return chars[0]
    if chars[-1] == '~':   #converts '~' to '-'
        del chars[-1]
        if chars[0] != '-': chars.insert(0,'-')
    priorityList = ('ACGT','N','-','acgt','n')
    for group in priorityList:
        matchs = [base for base in chars if group.find(base) != -1]
        if len(matchs) == 0: continue
        elif len(matchs) == 1: return matchs[0]
        else: return IUPAC(matchs)

def multRangeCallback(option, opt_str, value, parser):
    '''Version: 1.0
    Callback function for interpreting multiple range arguments from a command line in conjunction with the python module OptParse'''
    values = []
    def floatable(str):
        try:
            float(str)
            return True
        except ValueError: return False
    for arg in parser.rargs:         
        if arg[:2] == "--" and len(arg) > 2: break   # stop on --foo like options             
        if arg[:1] == "-" and len(arg) > 1 and not floatable(arg): break   # stop on -a, but not on -3 or -3.0
        values.append(arg)
    if len(values) == 0: errorExit("option '%s' requires an argument; none supplied." % option.dest)
    else:
        try:
            Ranges = []
            for value in values: 
                Range = value.split('-')
                if len(Range) != 2:
                    print Range
                    errorExit("option '%s' requires one argument, in the form of two numbers separated by a hyphen, such as 1.2-4.5; to only specify a maximum or minimum, omit the first or second number respectively, such as -4.5" % option.dest)
                if Range[0] == '': Range[0] = None
                else: Range[0] = float(Range[0])
                if Range[1] == '': Range[1] = None
                else: Range[1] = float(Range[1])
                Ranges.append(Range)
        except ValueError: errorExit("option '%s': cannot convert the argument '%s' to a number range; numerical values required." % (option.dest, value[0]))
        del parser.rargs[:len(values)]
        setattr(parser.values, option.dest, Ranges)

###Command Line Parseing###
cmndLineParser  = OptionParser(usage=progUsage, version="Version %s" % program_version)
nucmerGroup     = OptionGroup(cmndLineParser, "NUCmer-Related Modifiers") #Nucmer Modifiers
##Read filtering
cmndLineParser.add_option("-r",   "--quality-read-filter",       action="callback",      default=[[None, None]],    callback=multRangeCallback,    dest='quality_read_filter',\
                          help="Set the acceptable quality range(s) for reads. Reads outside this range will not be included in the consensus sequences.")
##Base filtering
cmndLineParser.add_option("-p",   "--proportion-base-filter",       action="callback",      default=[[None, None]],    callback=multRangeCallback,    dest='proportion_base_filter',\
                          help="Set the acceptable range(s) for the proportion of bases at a given position that support a given call. Nucleotides with outside of this range will be ignored when condensing the position to an IUPAC character.")
#cmndLineParser.add_option("-s",   "--SNP-quality-masking",       action="callback",      default=[],    callback=multRangeCallback,    dest='SNP_quality_masking',\
#                          help="Set the acceptable quality range(s) for masking. Bases outside this range will be masked")
##Position filtering
cmndLineParser.add_option("-f",   "--depth-position-filter",       action="callback",      default=[[1, None]],    callback=multRangeCallback,    dest='depth_position_filter',\
                          help="Set the depth range(s) for position filtering. Positions outside this range will not be included in the consensus sequences. (Default: 1-)")
##Position masking
cmndLineParser.add_option("-d",   "--depth-position-masking",       action="callback",      default=[[None, None]],    callback=multRangeCallback,    dest='depth_position_masking',\
                          help="Set the depth range(s) for position masking. Positions outside this range will be masked in the consensus sequences.")
#General options
cmndLineParser.add_option("-u",   "--include-unaligned",       action="store_true",      default=False,     dest='include_unaligned',\
                          help="Include the unaligned portions of the sequence in the output (Default: only output aligned regions.")
cmndLineParser.add_option("-N",   "--nucmer-location",       action="store",      default='nucmer',\
                          help="Specify the location of the nucmer executable.")
cmndLineParser.add_option(      '--touch',       action='store_true',    default=False,\
                          help='Load silently and do nothing.')
nucmerGroup.add_option(     "-n",   "--prefix",             action="store",         default="out",      type="string",  dest="prefix",          metavar="STRING",   help="Set the output file prefix (Default: out)")
nucmerGroup.add_option(     "-b",   "--break-length",       action="store",         default=200,        type="int",     dest="breaklen",        metavar="INT",      help="Distance an alignment extension will attempt to extend poor scoring regions before giving up (Default: 200)")
nucmerGroup.add_option(     "-j",   "--alternate-ref",      action="store",         default="",         type="string",  dest="alternate_ref",   metavar="INT",      help="Specify a new reference to be used in the rest of the alignment after yasra. (Default: use YASRA's reference)")
nucmerGroup.add_option(     "-t",   "--min-cluster",        action="store",         default=65,         type="int",     dest="mincluster",      metavar="INT",      help="Minimum cluster length used in the NUCmer analysis. (Default: 65)")
nucmerGroup.add_option(     "-k",   "--diag-factor",        action="store",         default=0.12,       type="float",   dest="diagfactor",      metavar="FLOAT",    help="Maximum diagonal difference factor for clustering, i.e. diagonal difference / match separation used by NUCmer. (Default: 0.12)")
nucmerGroup.add_option(     "-e",   "--no-extend",          action="store_true",    default=False,                      dest="noextend",                            help="Prevent alignment extensions from their anchoring clusters but still align the DNA between clustered matches in NUCmer. (Default: extend)")
nucmerGroup.add_option(     "-g",   "--forward-only",       action="store_true",    default=False,                      dest="forward",                             help="Align only the forward strands of each sequence. (Default: forward and reverse)")
nucmerGroup.add_option(     "-x",   "--max-gap",            action="store",         default=90,         type="int",     dest="maxgap",          metavar="INT",      help="Maximum gap between two adjacent matches in a cluster. (Default: 90)")             
nucmerGroup.add_option(     "-m",   "--min-match",          action="store",         default=20,         type="int",     dest="minmatch",        metavar="INT",      help="Minimum length of an maximal exact match. (Default: 20)")
nucmerGroup.add_option(     "-c",   "--coords",             action="store_true",    default=False,                      dest="coords",                              help="Automatically generate the <prefix>.coords file using the 'show-coords' program with the -r option. (Default: dont)")
nucmerGroup.add_option(     "-o",   "--no-optimize",        action="store_true",    default=False,                      dest="nooptimize",                          help="Toggle alignment score optimization. Setting --nooptimize will prevent alignment score optimization and result in sometimes longer, but lower scoring alignments (default: optimize)")
nucmerGroup.add_option(     "-s",   "--no-simplify",        action="store_true",    default=False,                      dest="nosimplify",                          help="Simplify alignments by removing shadowed clusters. Turn this option off if aligning a sequence to itself to look for repeats. (Default: simplify)")

cmndLineParser.add_option_group(nucmerGroup)
(options, args) = cmndLineParser.parse_args(argList)
if options.touch is False:
    if len(args) == 1:
        cmndLineParser.print_help()
        sys.exit(0)
    argNum = len(args) - 1   #counts the amount of arguments, negating the script name at the start of the command line
    if argNum != progArgNum: errorExit('%s takes exactly %d argument(s); %d supplied' % (program_name, progArgNum, argNum), 0)
    samPath, referencePath = args[-2], args[-1]
    ###


    ###Filtering and masking functions###
    def baseProportionFilter(positionData, proportionRanges = [[None, None]]):
        #NOTE: not efficient
        def removeAll(refList, delList, entry):
            for index in reversed(range(0,len(refList))):
                if refList[index] == entry:
                    del refList[index], delList[index]
        bases, baseIndexes = [], []
        for read, index, cigar in positionData:
            if cigar in readtools.cigarInsertTypes:
                bases.append(readtools.cigarInsertTypes[cigar])
            else:
                bases.append(read.seq[index])
        typeFrequency = readtools.getVariantFrequency(bases)
        depth = len(bases)
        for count, nucleotide in typeFrequency:
            proportion = float(count) / float(depth)
            if readtools.withinRanges(proportion, proportionRanges) == False:
                removeAll(bases, positionData, nucleotide)
        return positionData

    def getReadQuality(read):
        return read.quality

    def getPositionDepth(positionData):
        length = 0
        for read, index, cigar in positionData:
            if cigar in readtools.cigarAlignedTypes:
                length += 1
        return length


    ###

    ###Filter and masking initialization###
    readFilters     = [readtools.AttributeFilter(getReadQuality, options.quality_read_filter)]
    baseFilters     = [readtools.CustomizedFunction(baseProportionFilter, proportionRanges = options.proportion_base_filter)]
    positionFilters = [readtools.AttributeFilter(getPositionDepth, options.depth_position_filter)]
    positionMasking = [readtools.AttributeFilter(getPositionDepth, options.depth_position_masking)]
    ###

    ###Implimentation###
    contigPath = os.path.join(cwd, os.path.basename(samPath) + '.fa')
    pileups = list(readtools.PileupIO.parse(samPath, 'sam', applyPadding = False)) 
    ##Apply read filtering
    for pileup in pileups:
        for readFilter in readFilters:
            pileup.alignments = filter(readFilter, pileup.alignments)
        pileup.padAlignments()
    alignedContigsPath = contigPath + '_aligned.fa'
    #readtools.PileupIO.write(pileups, alignedContigsPath, 'fasta')
    ##Make contigs and save for nucmer
    contigs = [pileup.makeConsensus(baseFilters, positionFilters, positionMasking, IUPAC = False) for pileup in pileups]
    readtools.PileupAlignmentIO.write(contigs, contigPath, 'fasta')
    ##Align contigs with nucmer
    options.prefix = os.path.basename(contigPath)
    readtools.runNucmer(contigPath, referencePath, nucmer_path=options.nucmer_location, breaklen=options.breaklen, mincluster=options.mincluster, diagfactor=options.diagfactor, noextend=options.noextend,\
                        maxgap=options.maxgap, minmatch=options.minmatch, coords=options.coords, nooptimize=options.nooptimize, prefix=options.prefix,\
                        nosimplify=options.nosimplify, forward=options.forward)
    ##Apply nucmer alignments to contigs
    reference = list(readtools.PileupAlignmentIO.parse(referencePath, 'fasta'))[0] #Loads reference from file
    reference = readtools.PileupAlignment.fromAlignment(reference, cigar = '%dM' % len(reference.seq), start = 1)
    alignedContigsPath = contigPath + '_aligned.fa'
    alignedContigs = readtools.Pileup.fromNucmer(os.path.basename(contigPath) + '.delta', alignments = contigs)
    ##Save FASTA output
    #readtools.PileupIO.write(pileups, alignedContigsPath, 'fasta')
    if alignedContigs is not None:
        alignedContigs.alignments = [reference] + alignedContigs.alignments
        alignedContigs.padAlignments() #aligns to reference
        alignedContigs.alignments = alignedContigs.alignments[1:] #removes reference 
        contigsConsensus = alignedContigs.makeConsensus([], [], [], IUPAC = True)
        contigsConsensus.id = 'Consensus'
        alignedContigs.alignments = [reference, contigsConsensus] + alignedContigs.alignments
        readtools.PileupIO.write([alignedContigs], alignedContigsPath, 'fasta', includeUnalignedSequence = options.include_unaligned)
    ###

#This is the primary script responsible for the alignreads pipeline. 
#
#How to cite:
#
#Reference the following paper in which it was first described:
#Straub, S.C.K., M. Fishbein, T. Livshultz, Z. Foster, M. Parks, K. Weitemier, R.C. Cronn, A. Liston. 2011. Building a model: Developing genomic resources for common milkweed (Asclepias syriaca) with low coverage genome sequencing. BMC Genomics 12:211.

### Imports ###
import os, string, sys, time, copy, logging, tempfile, re
from optparse import *
from subprocess import *
######

### Functions ###
def import_file(full_path_to_module, name=None):
    try:
        import os
        module_dir, module_file = os.path.split(full_path_to_module)
        module_name, module_ext = os.path.splitext(module_file)
        save_cwd = os.getcwd()
        os.chdir(module_dir)
        module_obj = __import__(module_name)
        module_obj.__file__ = full_path_to_module
        if name is None:
            globals()[module_name] = module_obj
        else:
            globals()[name] = module_obj
        os.chdir(save_cwd)
        return module_obj
    except:
        raise 

def import_alignreads_component(component_name):
    try:
        installation_location = os.path.split(program_arguments[0])[0]
        component_location = os.path.join(installation_location, component_name + ".py")
        module_obj = import_file(component_location)
        return module_obj
    except:
        raise
def import_and_validate(component_name, accepted_versions):
    original_arguments = sys.argv[0]
    sys.argv = [component_name + '.py', '--touch']
    component = import_alignreads_component(component_name)
    sys.argv = original_arguments
    if component.program_version not in accepted_versions:
        raise ImportError("Wrong version of %s.py detected. Version found: %s\nCompatible Versions: %s" %\
                          (component.__name__, component.program_version, ", ".join(accepted_readtools_version)))

def floatable(str):
    try:
        float(str)
        return True
    except ValueError:
        return False

def multRangeCallback(option, opt_str, value, parser):
    '''Version: 1.0
    Callback function for interpreting multiple range arguments from a command line in conjunction with the python module OptParse'''
    values = []
    for arg in parser.rargs:         
        if arg[:2] == "--" and len(arg) > 2:
            break   # stop on --foo like options             
        if arg[:1] == "-" and len(arg) > 1 and not floatable(arg):
            break   # stop on -a, but not on -3 or -3.0
        values.append(arg)
    if len(values) == 0:
        errorExit("option '%s' requires an argument; none supplied." % option.dest)
    else:
        del parser.rargs[:len(values)]
        setattr(parser.values, option.dest, values)
            
def getOptCmndLine(args,converterKey):
    out = []
    for equivalancy in converterKey.iteritems(): #equivalancy = (alignreads option, yasra option) 
        option = getattr(args, equivalancy[0])
        if option != False and option != None: #if the option is a boolean and is the default value, therefore not nessesary (always false in this script)
            out.append(str(equivalancy[1]))
            if option != True:
                if type(option) != list: option = [option]
                for opt in option: out.append(str(opt))
    return out

def mvFiles(sourcePath, destinationPath):
    '''Version 1.1
    Moves all of the files from one directory to another.'''
    fileList = os.listdir(sourcePath)
    os.mkdir(destinationPath)
    for path in fileList:
        if os.path.isdir(path) == False:
            old = './' + path
            new = './' + os.path.basename(destinationPath) + '/' + path
            os.rename(old,new)

def saveCommandLine(path, commandLine):
    with open(path, 'a') as cmndLineOut:
        cmndLineOut.write(' '.join(commandLine) + '\n')

def validate_config(config_path, options):
    '''Checks if every option is in the configuration file path supplied. Raises an exception if any options are missing.'''
    try:
        with open(config_path, 'r') as config_handler:
            config_text = config_handler.read()
    except:
        print 'Could not load configuration file at supplied path "%s"' % config_path
        raise
    else:
        option_names = options.__dict__.keys()
        number_of_names_found = sum([name in config_text for name in options_names]) #Counts instances of "True"
        if number_of_names_found < len(option_names):
            raise TypeError('Invalid configuration file path at "%s". Could not find default values for all options. Uncoordinated changes to the code of alignreads cr the configuration file could casue this error' % config_path)

def execution_info_header():
    time_elapsed = float(time.clock() - start_time) / 60
    option_string = ''
    max_key_length = max([len(key) for key in options.__dict__.keys()])
    for key, value in options.__dict__.iteritems():
        option_string += '%s%s\t%s\n' % (key, ' '*(max_key_length - len(key)), value)
    return \
        '====== Alignreads Execution Information ======\n' +\
        'command line      \t%s\n' % ' '.join(program_arguments) +\
        'read file         \t%s\n' % yasra_query_path +\
        'reference file    \t%s\n' % yasra_reference_path +\
        'configuration file\t%s\n' % options.config_file +\
        'installation      \t%s\n' % installation_location +\
        'temp file location\t%s\n' % configuration.temporary_file_location+\
        '\n' +\
        '=== Option Values ===\n' +\
        option_string +\
        '\n' +\
        '=== Versions of constituent programs ===\n' +\
        'alignreads    \t%s\n' % program_version +\
        'lastz         \t%s\n' % lastz_version +\
        'readtools     \t%s\n' % readtools.program_version +\
        'makeconsensus \t%s\n' % makeconsensus.program_version +\
        'runyasra      \t%s\n' % runyasra.program_version +\
        'nucmer        \t%s\n' % nucmer_version +\
        '\n' +\
        '=== Execution statistics ===\n'+\
        'run time (m)  \t%0.2f\n' % time_elapsed +\
        '\n' +\
        '=== Run-time information ===\n'

def save_execution_info():
    try:
        if os.path.exists(alignreads_folder):
            log_location = os.path.join(alignreads_folder, configuration.execution_info_file_name)
        if os.path.exists(runyasra_folder):
            log_location = os.path.join(runyasra_folder, configuration.execution_info_file_name)
        if os.path.exists(new_folder_path):
            log_location = os.path.join(new_folder_path, configuration.execution_info_file_name)
    except:
        log_location = os.path.join(os.getcwd(), configuration.execution_info_file_name)
    header = execution_info_header()
    with open(temporary_log_file, 'r') as handle:
        log = handle.read()
    with open(log_location, 'w') as handle:
        handle.write(header)
        handle.write(log)
    os.remove(temporary_log_file)
    logging.shutdown()
        

######

### Import Alignreads Configuration File ###
if "--config-file" in sys.argv:
    try:
        configuration_path = sys.argv[sys.argv.index("--config-file") + 1]
    except IndexError:
        raise TypeError('No config-file argument found')
else:
    configuration_path = os.path.join(os.path.split(sys.argv[0])[0], "default_configuration.py")
import_file(configuration_path, name="configuration")
######

### Variable Initialization ###
temporary_file_id, temporary_log_file = tempfile.mkstemp(prefix=configuration.temporary_file_prefix, suffix=configuration.temporary_log_file_suffix, dir=configuration.temporary_file_location)
logging.basicConfig(filename = temporary_log_file, level = 'DEBUG', format = '[%(asctime)s]\t%(levelname)s\t%(module)s\t%(lineno)d\t%(message)s')
start_time = time.clock()
program_arguments = sys.argv #argument list supplied by user in its raw form
minimum_argument_number = 1 #the smallest amount of arguments with which it is possible to run the script
original_cwd = os.getcwd()
program_name = 'alignreads'
program_version = '2.4.0'
program_usage = 'python %s <Read FASTA File> <Reference FASTA File>  [options] OR...\n       python %s <Alignreads Output Folder> [options]' % (program_name, program_name)
accepted_lastz_versions = ['1.3.2', '1.03.02', '1.03.03', '1.3.3']
accepted_readtools_versions = ['1.0.0']
accepted_makeconesnsus_versions = ['1.1.1']
accepted_runyasra_versions = ['2.2.3']
accepted_nucmer_versions = ['3.1']
installation_location = os.path.split(sys.argv[0])[0]
runyasra_arguments = {'output_directory' : '--output-directory', 'lastz_location' : '--lastz-binary-path', 'yasra_location' : '--yasra-binary-path',\
                      'read_type' : '--read-type', 'read_orientation' : '--orientation', 'percent_identity' : '--percent-identity', 'single_step' : '--single-step',\
                      'external_makefile' : '--make-path'}
nucmer_arguments = {'break_length' : '--break-len', 'min_cluster' : '--min-cluster', 'diag_factor' : '--diag-factor', 'no_extend' : '--no-extend',\
                    'forward_only' : '--forward-only','max_gap' : '--max-gap', 'coords' : '--coords', 'no_optimize' : '--no-optimize', \
                    'no_simplify' : '--no-simplify', 'min_match' : '--min-match'}
makeconsensus_arguments = {'depth_position_filter' : '--depth-position-filter', 'quality_read_filter' : '--quality-read-filter',\
                           'depth_position_masking' : '--depth-position-masking', 'proportion_base_filter' : '--proportion-base-filter'}
run_id_default = None
print_log = []
######

###Command Line Parser Initilization###
command_line_parser = OptionParser(usage = program_usage, version = "Version %s" % program_version)
yasra_group = OptionGroup(command_line_parser, "YASRA-Related Modifiers") #Yasra Modifiers
makeconsensus_group = OptionGroup(command_line_parser, "makeConsensus-Related Modifiers") 
nucmer_group = OptionGroup(command_line_parser, "NUCmer-Related Modifiers") #Nucmer Modifiers
command_line_parser.add_option("-i", "--run-id", action="store", default=run_id_default, type="string",\
                               help="Used to identify the alignment generated. Is used in the folder names for each alignment. (Default: %s)" % run_id_default)
command_line_parser.add_option("-c", "--config-file", action="store", default=None, type="string",\
                               help="Supply the path to a alignreads configuration file to use its default parameters. (Default: Use default installation file)")
command_line_parser.add_option("-y", "--output-directory", action="store", default=configuration.output_directory, type="string", metavar="PATH",\
                               help="Specify where the output directory will be made. NOTE: this option only applies to new alignreads directoies. (Default: %s)" % configuration.output_directory)
yasra_group.add_option("-t", "--read-type", action="store", default=configuration.read_type, type="choice", dest="read_type", choices=["454","solexa"], metavar="454 or solexa",\
                       help="Specify the type of reads. (Default: %s)" % configuration.read_type)
yasra_group.add_option("-o", "--read-orientation", action="store", default=configuration.read_orientation, type="choice", dest="read_orientation", choices=["circular","linear"], metavar="circular or linear",\
                       help="Specify orientation of the sequence. (Default: %s" % configuration.read_orientation)
yasra_group.add_option("-p", "--percent-identity", action="store", default=configuration.percent_identity, type="choice", dest="percent_identity", choices=["same","high","medium","low","verylow","desperate"], metavar="same, high, medium, low or very low",\
                       help="The percent identity (PID in yasra). The settings correspond to different percent values depending on the read type (-t). (Defalt: %s)" % configuration.percent_identity)
yasra_group.add_option("-a", "--single-step", action="store_true", default=configuration.single_step, dest="single_step",\
                       help="Activate yasra's single_step option (Default: %s)" % configuration.single_step)
yasra_group.add_option("-e", '--yasra-location', action='store', default=configuration.yasra_location, type='string', metavar='PATH',\
                       help="Specify path binaries used by YASRA. (Default: %s)" % configuration.yasra_location)
yasra_group.add_option("-l", '--lastz-location', action='store', default=configuration.lastz_location, type='string', metavar='PATH',\
                       help="Specify path binaries used by lastz. (Default: %s)" % configuration.lastz_location)
yasra_group.add_option("-E", "--external-makefile", action="store", default=configuration.external_makefile, type="string", dest="external_makefile", metavar="FILEPATH",\
                       help="Specify path to external makefile used by YASRA. (Default: use the makefile built in to runyasra)")
nucmer_group.add_option("-q", "--break-length", action="store", default=configuration.break_length, type="int", dest="break_length", metavar="INT",\
                        help="Distance an alignment extension will attempt to extend poor scoring regions before giving up (Default: %d)" % configuration.break_length)
nucmer_group.add_option("-j", "--alternate-reference", action="store", default=configuration.alternate_reference, type="string", dest="alternate_ref", metavar="INT",\
                        help="Specify a new reference to be used in the rest of the alignment after yasra. (Default: use YASRA's reference)")
nucmer_group.add_option("-A", "--anchor-uniqueness", action="store", default=configuration.anchor_uniqueness, type="choice", dest="anchor_uniqueness", choices=["mum","ref","max"], metavar="mum, ref, or max",\
                        help="Specify how NUCmer chooses anchor matches using one of three settings: mum = Use anchor matches that are unique in both the reference and query, ref =  Use anchor matches that are unique in the reference but not necessarily unique in the query, max = Use all anchor matches regardless of their uniqueness. (Default = %s)" % configuration.anchor_uniqueness)
nucmer_group.add_option("-T", "--min-cluster", action="store", default=configuration.min_cluster, type="int", dest="min_cluster", metavar="INT",\
                        help="Minimum cluster length used in the NUCmer analysis. (Default: %d)" % configuration.min_cluster)
nucmer_group.add_option("-D", "--diag-factor", action="store", default=configuration.diag_factor, type="float", dest="diag_factor", metavar="FLOAT",\
                        help="Maximum diagonal difference factor for clustering, i.e. diagonal difference / match separation used by NUCmer. (Default: %0.2f)" % configuration.diag_factor)
nucmer_group.add_option("-J", "--no-extend", action="store_true", default=configuration.no_extend, dest="no_extend",\
                        help="Prevent alignment extensions from their anchoring clusters but still align the DNA between clustered matches in NUCmer. (Default: %s)" % configuration.no_extend)
nucmer_group.add_option("-F", "--forward-only", action="store_true", default=configuration.forward_only, dest="forward_only",\
                        help="Align only the forward strands of each sequence. (Default: %s)" % configuration.forward_only)
nucmer_group.add_option("-X", "--max-gap", action="store", default=configuration.max_gap, type="int", dest="max_gap", metavar="INT",\
                        help="Maximum gap between two adjacent matches in a cluster. (Default: %s)" % configuration.max_gap)             
nucmer_group.add_option("-M", "--min-match", action="store", default=configuration.min_match, type="int", dest="min_match", metavar="INT",\
                        help="Minimum length of an maximal exact match. (Default: %d)" % configuration.min_match)
nucmer_group.add_option("-C", "--coords", action="store_true", default=configuration.coords, dest="coords",\
                        help="Automatically generate the <prefix>.coords file using the 'show-coords' program with the -r option. (Default: %s)" % configuration.coords)
nucmer_group.add_option("-O", "--no-optimize", action="store_true", default=configuration.no_optimize, dest="no_optimize",\
                        help="Toggle alignment score optimization. Setting --nooptimize will prevent alignment score optimization and result in sometimes longer, but lower scoring alignments (default: %s)" % configuration.no_optimize)
nucmer_group.add_option("-S", "--no-simplify", action="store_true", default=configuration.no_simplify, dest="no_simplify",\
                        help="Simplify alignments by removing shadowed clusters. Turn this option off if aligning a sequence to itself to look for repeats. (Default: %s)" % configuration.no_simplify)
makeconsensus_group.add_option("-g", "--quality-read-filter", action="callback", default=configuration.quality_read_filter, callback=multRangeCallback, dest='quality_read_filter',\
                               help="Set the acceptable quality range(s) for reads. Reads outside this range will not be included in the consensus sequences. (Default: %s)" % configuration.quality_read_filter)
makeconsensus_group.add_option("-m", "--depth-position-masking", action="callback", default=configuration.depth_position_masking, callback=multRangeCallback, dest='depth_position_masking',\
                               help="Set the depth range(s) for position masking. Positions outside this range will be masked in the consensus sequences. (Default: %s)" % configuration.depth_position_masking)
makeconsensus_group.add_option("-b", "--proportion-base-filter", action="callback", default=configuration.proportion_base_filter, callback=multRangeCallback, dest='proportion_base_filter',\
                               help="Set the acceptable range(s) for the proportion of bases at a given position that support a given call. Nucleotides with outside of this range will be ignored when condensing the position to an IUPAC character. (Default: %s)" % configuration.proportion_base_filter)
makeconsensus_group.add_option("-d", "--depth-position-filter", action="callback", default=configuration.depth_position_filter, callback=multRangeCallback, dest='depth_position_filter',\
                               help="Set the depth range(s) for position filtering. Positions outside this range will not be included in the consensus sequences. (Default: %s)" % configuration.depth_position_filter)
(options, arguments) = command_line_parser.parse_args(sys.argv[1:])
if options.output_directory is None:
    options.output_directory = os.getcwd()
if options.config_file is None:
    options.config_file = os.path.join(installation_location, "default_configuration.py")
    if os.path.exists(options.config_file) is False:
        error_text = 'Could not find default configuration file "%s" and a alternative was not specified.' % options.config_file
        logging.fatal(error_text)
        raise Exception(error_text)
######

### Help Menu ###
if len(arguments) == 0: #if no arguments are supplied
    command_line_parser.add_option_group(yasra_group)
    command_line_parser.add_option_group(nucmer_group)
    command_line_parser.add_option_group(makeconsensus_group)
    command_line_parser.print_help()
    sys.exit(0)
######

### Argument Validation ###
logging.debug('Validating input arguments...')
if len(arguments) == 1:
    if os.path.isdir(arguments[0]) is False:
        error = '[alignreads] Path supplied is not a directory. Alignreads takes either 1 directory or 2 files as arguments.' % str(len(arguments))
        logging.fatal(error)
        raise ValueError(error)
elif len(arguments) == 2:
    if os.path.isfile(arguments[0]) is False:
        error = '[alignreads] First path supplied is not a file. Alignreads takes either 1 directory or 2 files as arguments.' % str(len(arguments))
        logging.fatal(error)
        raise ValueError(error)
    if os.path.isfile(arguments[1]) is False:
        error = '[alignreads] Second path supplied is not a file. Alignreads takes either 1 directory or 2 files as arguments.' % str(len(arguments))
        logging.fatal(error)
        raise ValueError(error)
elif len(arguments) > 2:
    error = '[alignreads] Too many argments supplied. Alignreads takes either 1 directory or 2 files as arguments. %s arguments supplied...' % str(len(arguments))
    logging.fatal(error)
    raise ValueError(error)
logging.debug('Validating input arguments complete.')
######

### Alignreads Component Version Verification ###
logging.debug('Checking versions of alignreads components...')
import_and_validate("readtools", accepted_readtools_versions)
import_and_validate("runyasra", accepted_runyasra_versions)
import_and_validate("makeconsensus", accepted_makeconesnsus_versions)
logging.debug('Checking versions of alignreads components complete.')
######

### Lastz Version Verification ###
logging.debug('Checking version of lastz...')
try:
    process = Popen([configuration.lastz_location, "-v"], stdout=PIPE)
    process.wait()
    lastz_output = process.stdout.read()
    lastz_version = re.search('version ([0123456789.]*) ', lastz_output).group(1)
    if lastz_version not in accepted_lastz_versions:
        raise readtools.InputValidationError("[alignreads] Wrong version of LASTZ detected. Version found: '%s'.  Compatible Versions: '%s'" %\
                                             (lastz_version, ", ".join(accepted_lastz_versions)))
except:
    logging.fatal('An unknown error occured during validation of LASTZ:')
    raise
logging.debug('Checking version of lastz complete.')
######

### Nucmer Version Verification ###
logging.debug('Checking version of nucmer...')
try:
    process = Popen([configuration.nucmer_location, "-v"], stdout=PIPE, stderr=STDOUT)
    process.wait()
    nucmer_output = process.stdout.read()
    nucmer_version = re.search('version ([0123456789.]*)', nucmer_output).group(1)
    if nucmer_version not in accepted_nucmer_versions:
        raise readtools.InputValidationError("Wrong version of LASTZ detected. Version found: '%s'.  Compatible Versions: '%s'" %\
                                             (nucmer_version, ", ".join(accepted_nucmer_versions)))
except:
    logging.fatal("An unknown error occured during validation of nucmer:")
    raise
logging.debug('Checking version of nucmer complete.')
######

### Execution of Runyasra ###
try:
    if len(arguments) == 2: #if runyasra is to be used...
        logging.debug('Executing runyasra...')
        yasra_query_path = os.path.abspath(arguments[0])
        yasra_reference_path = os.path.abspath(arguments[1])
        runyasra_command_line = ['runyasra.py'] + getOptCmndLine(options,runyasra_arguments) + [yasra_query_path, yasra_reference_path]
        sys.argv = runyasra_command_line
        logging.info('Implimenting YASRA with runyasra.py using the following command line:\n %s' % ' '.join(runyasra_command_line))
        try:
            reload(runyasra)
        except readtools.InputValidationError as error:
            raise
        except readtools.YasraFailure as error:
            raise
        except:
            logging.exception("An unknown error occured during runyasra.")
            raise
        else: #if runyasra completed
            alignreads_folder = runyasra.outDirPath
            runyasra_folder = os.path.join(alignreads_folder, configuration.yasra_subfolder_name)
            command_line_record_file_path = os.path.join(runyasra_folder, configuration.command_line_record_file_name)
            saveCommandLine(configuration.command_line_record_file_name, runyasra_command_line)    
            mvFiles(alignreads_folder, runyasra_folder)
        logging.debug('Execution of runyasra complete...')
######

### Determination of read and reference files from previous runyasra output ###
    elif len(arguments) == 1: #if the user supplied the folder of a previous yasra run, insead of running it again
        logging.debug('Extracting information from previous alignreads run...')
        alignreads_folder = os.path.abspath(arguments[0])
        runyasra_folder = os.path.join(alignreads_folder, configuration.yasra_subfolder_name)
        makefile_path = os.path.join(runyasra_folder, 'Makefile') #reads makefile
        with open(makefile_path, 'r') as makefile_handle:
            makefile = makefile_handle.readlines()
        for line in makefile: #the makefile used in the previously run yasra folder is searched to find the names of the input files
            if line.find('READS=') == 0:
                yasra_query_path = line.strip().replace('READS=','')
            elif line.find('TEMPLATE=') == 0:
                yasra_reference_path = line.strip().replace('TEMPLATE=','')
                break
        logging.debug('Extraction of information from previous alignreads run complete.')
######

### Generation of New Alignment Folder ###
    try:
        logging.debug('Preparing output folder for post-yasra anaylsis....')
        alignment_folders = [name for name in os.listdir(alignreads_folder) if os.path.isdir(os.path.join(alignreads_folder, name)) and\
                             re.match("%s_(\S+_)?\d+" % configuration.make_consensus_sub_folder_name, name) is not None]
        if len(alignment_folders) > 0:
            highest_count = max([int(re.match("%s_(\S+_)?(\d+)" % configuration.make_consensus_sub_folder_name, name).groups()[1]) for name in alignment_folders])
        else:
            highest_count = 0
        new_folder_name = '%s' % configuration.make_consensus_sub_folder_name
        if options.run_id is not None:
            new_folder_name = '%s_%s_%d' % (configuration.make_consensus_sub_folder_name, options.run_id, highest_count + 1)
            count = 2
            while new_folder_name in alignment_folders:
                new_folder_name = '%s_%s(%d)_%d' % (configuration.make_consensus_sub_folder_name, options.run_id, count, highest_count + 1)
                count += 1
        else:
            new_folder_name = '%s_%d' % (configuration.make_consensus_sub_folder_name, highest_count + 1)
        new_folder_path = os.path.join(alignreads_folder, new_folder_name)
        os.mkdir(new_folder_path)
    except:
        logging.exception('An unknown error occured during creation of new alignment folder')
        raise
    else:
        logging.debug('Prepartion of output folder for post-yasra anaylsis complete.')
######

### Execution of makeconsensus.py ###
    logging.debug('Executing makeconsensus...')
    yasra_query_link_path = os.path.join(runyasra_folder, os.path.basename(yasra_query_path))
    yasra_reference_link_path = os.path.join(runyasra_folder, os.path.basename(yasra_reference_path))
    sam_path = os.path.join(runyasra_folder, 'alignments_%s_%s.sam' % (os.path.basename(yasra_query_link_path), os.path.basename(yasra_reference_link_path)))
    makeconsensus_command_line = ['makeConsensus.py'] + [sam_path, yasra_reference_link_path] +\
                                 getOptCmndLine(options,makeconsensus_arguments) +\
                                 getOptCmndLine(options,nucmer_arguments)    
    try:
        os.chdir(new_folder_path)
        sys.argv = makeconsensus_command_line
        reload(makeconsensus)
    except:
        logging.fatal('An error occured during execution of makeconsensus.py:')
        raise
    else:
        sys.argv = program_arguments
        os.chdir(original_cwd)
    finally:
        os.chdir(original_cwd)
        sys.argv = program_arguments
        logging.debug('Execution of makeconsensus complete.')
######

### Log File and Clean Up ###
except:
    save_execution_info()
    raise
else:
    save_execution_info()

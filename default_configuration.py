#This file is used to store default parameters for every option of alignreads.
#DO NOT modify the copy of this file in the installation directory, HOWEVER you are encouraged to make copies of this file and customize them to suit specific tasks. 
#Files of this type are referenced by alignreads, but are independent of any one installation of alignreads. 

### YASRA Options ###
output_directory = None
read_type = "solexa"
read_orientation = "circular"
percent_identity = "same"
single_step = False
yasra_location = None
lastz_location = None
external_makefile = False
######

### Nucmer Options ###
break_length = 200
alternate_reference = ""
anchor_uniqueness = "ref"
min_cluster = 65
diag_factor = 0.12
no_extend = False
forward_only = False
max_gap = 90
min_match = 20
coords = False
no_optimize = False
no_simplify = False
######

### makeconsensus Options ###
quality_read_filter = None
depth_position_masking = None
proportion_base_filter = None
depth_position_filter = None 
nucmer_location = None
python_location = None
######

yasra_subfolder_name = 'YASRA_related_files'
make_consensus_sub_folder_name = 'alignment'
command_line_record_file_name = 'Command_Line_Record.txt'
execution_info_file_name = 'Execution_info.txt'

temporary_file_location = None
temporary_file_prefix = 'alignreads_temporary_'
temporary_log_file_suffix = 'log.txt'



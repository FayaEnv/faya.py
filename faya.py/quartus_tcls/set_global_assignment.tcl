# Script to add Verilog file to Quartus project
# Usage: quartus_sh -t set_global_assignment.tcl <project_name> <verilog_file>

if {$argc != 3} {
    puts "Error: Incorrect number of arguments"
    puts "Usage: quartus_sh -t set_global_assignment.tcl <project_name> <type> <file>"
    exit 1
}

set project_name [lindex $argv 0]
set type [lindex $argv 1]
set file [lindex $argv 2]

# Check if project exists
if {![file exists ${project_name}.qpf]} {
    puts "Error: Project ${project_name}.qpf not found"
    exit 1
}

# Check if Verilog file exists
#if {![file exists $file]} { # ignore this (in case of not files)
#    puts "Error: $type file $file not found"
#    exit 1
#}

# Open project
project_open $project_name

# Add Verilog file to project
if {[catch {
    set_global_assignment -name $type $file
    export_assignments
} error_msg]} {
    puts "Error: Failed to add Verilog file: $error_msg"
    project_close
    exit 1
}

puts "Successfully added $file to project $project_name"

# Close project
project_close
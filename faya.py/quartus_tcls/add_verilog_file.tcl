# Script to add Verilog file to Quartus project
# Usage: quartus_sh -t add_verilog_file.tcl <project_name> <verilog_file>

if {$argc != 2} {
    puts "Error: Incorrect number of arguments"
    puts "Usage: quartus_sh -t add_verilog_file.tcl <project_name> <verilog_file>"
    exit 1
}

set project_name [lindex $argv 0]
set verilog_file [lindex $argv 1]

# Check if project exists
if {![file exists ${project_name}.qpf]} {
    puts "Error: Project ${project_name}.qpf not found"
    exit 1
}

# Check if Verilog file exists
if {![file exists $verilog_file]} {
    puts "Error: Verilog file $verilog_file not found"
    exit 1
}

# Open project
project_open $project_name

# Add Verilog file to project
if {[catch {
    set_global_assignment -name VERILOG_FILE $verilog_file
    export_assignments
} error_msg]} {
    puts "Error: Failed to add Verilog file: $error_msg"
    project_close
    exit 1
}

puts "Successfully added $verilog_file to project $project_name"

# Close project
project_close
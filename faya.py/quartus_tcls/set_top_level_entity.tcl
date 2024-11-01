# Script to add Verilog file to Quartus project
# Usage: quartus_sh -t set_top_level_entity.tcl <project_name> <top_level_entity>

if {$argc != 2} {
    puts "Error: Incorrect number of arguments"
    puts "Usage: quartus_sh -t set_top_level_entity.tcl <project_name> <top_level_entity>"
    exit 1
}

set project_name [lindex $argv 0]
set top_level_entity [lindex $argv 1]

# Check if project exists
if {![file exists ${project_name}.qpf]} {
    puts "Error: Project ${project_name}.qpf not found"
    exit 1
}

# Open project
project_open $project_name

# Add Verilog file to project
if {[catch {
    set_global_assignment -name TOP_LEVEL_ENTITY $top_level_entity
    export_assignments
} error_msg]} {
    puts "Error: Failed to set TOP_LEVEL_ENTITY: $error_msg"
    project_close
    exit 1
}

puts "Successfully added $top_level_entity to project $project_name"

# Close project
project_close
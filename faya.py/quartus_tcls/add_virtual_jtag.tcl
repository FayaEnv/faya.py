# Apri un nuovo progetto IP con Platform Designer
load_package IP

# Crea un nuovo sistema Platform Designer (nome del sistema: "virtual_jtag_system")
project_new virtual_jtag_system

# Aggiungi il core Virtual JTAG
set_instance_parameter_value altera_virtual_jtag_0 altera_virtual_jtag enabled 1
set_instance_parameter_value altera_virtual_jtag_0 altera_virtual_jtag INSTANCE_ID "0"
set_instance_parameter_value altera_virtual_jtag_0 altera_virtual_jtag IR_WIDTH "4"

# Salva il sistema come un file Qsys
save_system_as virtual_jtag_system.qsys

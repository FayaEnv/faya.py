import os.path

from libs.yaml import *
from libs.debug import *
from libs.this_platform import *
from libs.paths import *
from libs.qmegawiz import *
from libs.execution import *
from libs.quartus_search import *

# Global vars
quartus_dir = None

class QuartusAutomation:
    def __init__(self, quartus_dir, board_name, project_name):
        """
        Inizializza l'automazione di Quartus

        Args:
            quartus_dir (str): Percorso della directory di installazione di Quartus
            board_name (str): Nome del progetto/top level entity
        """
        self.quartus_dir = Path(quartus_dir)

        self.project_name = project_name

        self.project_dir = './projects/' + self.project_name
        create_directory(self.project_dir)

        self.quartus_bin = self.quartus_dir / "bin64"

        # Verifica che la directory di Quartus esista
        if not self.quartus_dir.exists():
            raise FileNotFoundError(f"Directory Quartus non trovata: {self.quartus_dir}")

        # Get board infos
        # Read the YAML file
        device = read_yaml_file("boards/"+board_name+".yaml")

        self.board_name = board_name
        self.device = device
        self.board = board = device['board']
        self.device_code = board['name']
        self.device_family = board["device_family"]
        self.device_part = board["device"]

        # Print the configuration
        #print_quartus_config(board)

    def get_board_path(self):
        return get_faya_path() / "boards" / self.board_name

    def create_virtual_jtag(self):

        '''
        tcls = str(get_faya_path()) + '/quartus_tcls'

        cmd = [
            check_exe(str(self.quartus_bin / 'quartus_sh')),
            f'-t "{tcls}/add_virtual_jtag.tcl"'
        ]

        run_quartus(cmd, working_dir=self.project_dir)
        '''

        ip_core = "Virtual_JTag"

        copy_files(ip_core, self.project_dir)

        ip_path = ip_core+'.qsys'
        if os.path.exists(ip_path):
            #qsys-generate virtual_jtag_system.qsys --synthesis=VERILOG
            cmd = [
                check_exe(quartus_dir + '/sopc_builder/bin/qsys-generate'),
                f'"{ip_path}" --synthesis=VERILOG'
            ]

            run_quartus(cmd, working_dir=self.project_dir)

            #quartus_sh --flow compile nome_progetto
            cmd = [
                check_exe(str(self.quartus_bin / 'quartus_sh')),
                f'--flow compile {self.project_name}'
            ]

            run_quartus(cmd, working_dir=self.project_dir)

        print("IP Core added")

    def create_project(self, verilog_files):
        """
        Crea un nuovo progetto Quartus

        Args:
            verilog_files ([str]): Percorso del file Verilog
            device (object): Board device infos
        """

        device = self.device
        board = self.board

        quartus_sh = self.quartus_bin / check_exe("quartus_sh")

        # Crea il progetto
        if board['copy_project']:
            board_path = self.get_board_path()
            base_proj = board_path / "base.qsf"
            copy_and_rename(base_proj, self.project_dir, self.project_name+".qsf")
        else:
            cmd = [
                str(quartus_sh),
                "--tcl_eval",
                f'project_new -overwrite -part {self.device_part} {self.project_name}'
            ]
            run_quartus(cmd, working_dir=self.project_dir)

        tcls = str(get_faya_path()) + '/quartus_tcls'

        # Aggiungi il file Verilog
        for verilog_file in verilog_files:
            cmd = [
                str(quartus_sh),
                f'-t "{tcls}"/add_verilog_file.tcl',
                f'"{self.project_name}" "{verilog_file}"'
            ]
            run_quartus(cmd, working_dir=self.project_dir)

        # Create Virtual JTag
        self.create_virtual_jtag()

        # Aggiungi il file SDC se specificato
        sdc_file = str(get_faya_path()) + '/boards/'+device['board']['name']+'/base.SDC'
        if exists(sdc_file):
            print(f"Aggiunta file SDC: {sdc_file}")
            cmd = [
                str(quartus_sh),
                f'-t "{tcls}/set_global_assignment.tcl"',
                f'"{self.project_name}" "SDC_FILE" "{sdc_file}"'
            ]
            run_quartus(cmd, working_dir=self.project_dir)

            # Abilita l'analisi temporale
            cmd = [
                str(quartus_sh),
                f'-t "{tcls}/set_global_assignment.tcl"',
                f'"{self.project_name}" "ENABLE_ADVANCED_IO_TIMING" "ON"'
            ]
            run_quartus(cmd, working_dir=self.project_dir)

        # Imposta il top level entity
        cmd = [
            str(quartus_sh),
            f'-t "{tcls}"/set_top_level_entity.tcl',
            f'"{self.project_name}" "{self.project_name}"'
        ]
        run_quartus(cmd, working_dir=self.project_dir)

    def set_quartus_settings(self, clock_freq, voltage=1.2):
        """
        Set voltage and clock frequency settings for a Quartus project using quartus_sh

        Args:
            clock_freq: Clock frequency in MHz
            voltage: Target voltage in volts
        """

        project_path = self.project_dir + '/' + (self.project_name + '.qpf')

        try:
            # Ensure project path exists
            if not os.path.exists(project_path):
                raise FileNotFoundError(f"Project file not found: {project_path}")

            # Get project name without extension
            project_name = self.project_name

            # Create Tcl commands
            tcl_commands = [
                f'project_open {project_name}',
                # Set core voltage to 3.2V
                f'set_global_assignment -name CORE_VOLTAGE {voltage}V',
                # Set clock frequency to 50MHz (convert to Hz)
                f'set_global_assignment -name CLOCK_FREQUENCY {int(clock_freq * 1e6)}',
                'export_assignments',
                'project_close'
            ]

            # Join commands with semicolons
            tcl_script = '; '.join(tcl_commands)

            quartus_sh = self.quartus_bin / check_exe("quartus_sh")

            # Run quartus_sh with Tcl commands
            cmd = [str(quartus_sh), '-t', 'tcl_script']
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # Send Tcl commands to quartus_sh
            stdout, stderr = process.communicate(input=tcl_script)

            if process.returncode != 0:
                print(f"Error: quartus_sh returned code {process.returncode}")
                print(f"stderr: {stderr}")
                return False

            print("Successfully updated Quartus project settings:")
            print(f"- Core Voltage: {voltage}V")
            print(f"- Clock Frequency: {clock_freq}MHz")
            return True

        except Exception as e:
            print(f"Error: {str(e)}")
            return False

    def compile_project(self):
        """
        Compila il progetto usando quartus_map, quartus_fit e quartus_asm
        """
        print("Iniziando la compilazione...")

        # Analysis & Synthesis
        run_quartus([
            str(self.quartus_bin / check_exe("quartus_map")),
            "--read_settings_files",
            "--write_settings_files=off",
            self.project_name,
            f"--rev={self.project_name}"
        ], working_dir=self.project_dir)

        # Fitter
        run_quartus([
            str(self.quartus_bin / check_exe("quartus_fit")),
            "--read_settings_files",
            "--write_settings_files=off",
            self.project_name,
            f"--rev={self.project_name}"
        ], working_dir=self.project_dir)

        # Assembler
        run_quartus([
            str(self.quartus_bin / check_exe("quartus_asm")),
            "--read_settings_files",
            "--write_settings_files=off",
            self.project_name,
            f"--rev={self.project_name}"
        ], working_dir=self.project_dir)

    def program_device(self, mode='jtag'):
        """
        Programma il dispositivo usando il programmatore USB-Blaster

        Args:
            mode (str): Modalità di programmazione ("JTAG" o "EPCS")
        """
        print("\nProgrammazione del dispositivo...")

        # Set project voltage
        #self.set_quartus_settings(50, 3.2) # seems useless

        # Cerca il programmatore USB-Blaster
        result = run_quartus([str(self.quartus_bin/"quartus_pgm"), "-l"], working_dir=self.project_dir)

        if "USB-Blaster" not in result:
            raise RuntimeError("USB-Blaster non trovato. Assicurati che sia collegato e riconosciuto.")

        # Determina il file e le opzioni in base alla modalità
        if mode.upper() == "EPCS":
            # Genera il file .pof dalla conversione del .sof
            sof_file = f"{self.project_name}.sof"
            pof_file = f"{self.project_name}.pof"

            if not os.path.exists(self.project_dir + '/' + sof_file):
                raise FileNotFoundError(f"File .sof non trovato: {sof_file}")

            print("Conversione .sof in .pof per programmazione EPCS...")
            run_quartus([str(self.quartus_bin/"quartus_cpf"),
                "-c",  # Modalità di conversione
                sof_file,  # File di input
                pof_file,  # File di output
                f'-d "../../boards/{self.device_code}/device.qar"' #todo: set device file
            ], working_dir=self.project_dir)

            # Programma il dispositivo usando il file .pof
            run_quartus([str(self.quartus_bin.parent / "qprogrammer" / "bin64" / "quartus_pgm"),
                "-c", "USB-Blaster",
                "-m", "AS",  # Active Serial programming
                "-o", f"P;{pof_file}"  # Program operation
            ], working_dir=self.project_dir)

        else:  # JTAG mode
            sof_file = f"{self.project_name}.sof"
            if not os.path.exists(self.project_dir + '/' + sof_file):
                raise FileNotFoundError(f"File .sof non trovato: {sof_file}")

            # quartus_pgm = self.quartus_bin.parent.parent / "qprogrammer" / "bin64" / check_exe("quartus_pgm") # valid on Quartus Lite
            quartus_pgm = self.quartus_bin / check_exe("quartus_pgm")

            run_quartus([str(quartus_pgm),
                "-c", "USB-Blaster",
                "-m", "JTAG",
                "-o", f"P;{sof_file}",
                "--program"
            ], working_dir=self.project_dir)

        print("Programmazione completata con successo!")


def main():
    global quartus_dir

    print("Usage: python main.py <quartus_dir> <board_name> [<verilog_file>]")
    if len(sys.argv) < 3 and False: # use default values
        sys.exit(1)

    verilog_files = [ # with example files
        #r"""C:\Users\Riccardo Cecchini\Documents\DE0-Nano\DE0-Nano_v.1.2.8_SystemCD\Tools\DE0_Nano_SystemBuilder\CodeGenerated\DE0_NANO\DE0_NANO\DE0_NANO.v""",
        #r"""C:\Users\Riccardo Cecchini\Documents\DE0-Nano\DE0-Nano_v.1.2.8_SystemCD\Tools\DE0_Nano_SystemBuilder\CodeGenerated\DE0_NANO\DE0_NANO\vjtag_interface.v"""
        './verilogs/helloworld/DE0_NANO.v',
        './verilogs/helloworld/vjtag_interface.v'
    ]

    arg_num = 1
    quartus_dir = sys.argv[arg_num] if len(sys.argv) > arg_num else 'C:\\intelFPGA_lite\\23.1std\\quartus' #'C:\\altera\\13.1\\quartus'

    arg_num += 1
    board_name = sys.argv[arg_num] if len(sys.argv) > arg_num else 'de0_nano'

    arg_num += 1
    project_name = sys.argv[arg_num] if len(sys.argv) > arg_num else 'DE0_NANO'

    arg_num += 1
    if len(sys.argv) > arg_num:
        verilog_files.append(sys.argv[arg_num])

    try:
        automation = QuartusAutomation(quartus_dir, board_name, project_name)

        # Crea e compila il progetto
        automation.create_project(verilog_files)
        automation.compile_project()

        # Programma il dispositivo
        automation.program_device()

        print("Processo completato con successo!")

    except Exception as e:
        if is_debug_mode():
            raise e

        print(f"Errore: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
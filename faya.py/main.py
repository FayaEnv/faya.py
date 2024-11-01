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

    def create_virtual_jtag(self, instance_name="sld_virtual_jtag"):
        """
        Crea e configura l'IP Virtual JTAG

        Args:
            instance_name (str): Nome dell'istanza dell'IP Virtual JTAG
        """
        print(f"\nCreazione IP Virtual JTAG ({instance_name})...")

        ip_info = QuartusIPInfo(quartus_dir)
        ip_files = ip_info.get_ip_files('sld_virtual_jtag')

        # Crea il file QIP per il Virtual JTAG
        qip_content = f"""
            set_global_assignment -name IP_TOOL_NAME "Virtual JTAG Intel FPGA IP"   
            set_global_assignment -name IP_TOOL_VERSION "13.1"         
            set_global_assignment -name IP_GENERATED_DEVICE_FAMILY "{{{self.device_family}}}"
            set_global_assignment -name VERILOG_FILE [file join $::quartus(qip_path) "sld_virtual_jtag.v"]
            set_global_assignment -name MISC_FILE [file join $::quartus(qip_path) "sld_virtual_jtag_basic.v"]
            """

        qip_name = f"{instance_name}.qip"
        qip = f"{self.project_dir}/{qip_name}"
        with open(qip, "w") as f:
            f.write(qip_content)

        # Crea il file di parametrizzazione per il Virtual JTAG
        params = { # e questo?
            "device_family": self.device_family,
            "gui_use_auto_index": "true",
            "sld_auto_instance_index": "YES",
            "sld_instance_index": "0",
            "sld_ir_width": "1"
        }

        # Crea il comando per qsys-generate
        qsys_generate = self.quartus_dir / "sopc_builder" / "bin" / check_exe("qsys-generate")
        cmd = [
            str(qsys_generate),
            "--synthesis=VERILOG",
            f"--output-directory={instance_name}_output",
            f'--family="{self.device_family}"',
            "--part=" + self.device_part,
            qip_name
        ]

        tcls = str(get_faya_path()) + '/quartus_tcls'

        try:
            run_quartus(cmd, working_dir=self.project_dir)
            print(f"IP Virtual JTAG creato con successo")

            # Aggiungi i file generati al progetto
            run_quartus("quartus_sh", [
                "--tcl_eval",
                f"set_global_assignment -name QIP_FILE {qip_name}"
            ], working_dir=self.project_dir)

            cmd = [
                str("quartus_sh"),
                f'-t "{tcls}"/set_global_assignment.tcl',
                f'"{self.project_name}" "QIP_FILE" "{qip_name}"'
            ]
            run_quartus(cmd, working_dir=self.project_dir)

        except subprocess.CalledProcessError as e:
            print(f"Errore durante la generazione dell'IP Virtual JTAG: {e}")
            raise

    def create_project(self, verilog_files, device=None):
        """
        Crea un nuovo progetto Quartus

        Args:
            verilog_files ([str]): Percorso del file Verilog
            device (object): Board device infos
        """

        if device is None:
            raise Exception("Device parameters mandatory")

        self.device = device
        self.device_family = device['board']["device_family"]
        self.device_part = device['board']["device"]

        quartus_sh = self.quartus_bin / check_exe("quartus_sh")

        # Crea il progetto
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
        sdc_file = str(get_faya_path()) + '/boards/'+device['board']['name']+'.SDC'
        if exists(sdc_file):
            print(f"Aggiunta file SDC: {sdc_file}")
            cmd = [
                str(quartus_sh),
                f'-t "{tcls}"/set_global_assignment.tcl',
                f'"{self.project_name}" "SDC" "{sdc_file}"'
            ]
            run_quartus(cmd)

            # Abilita l'analisi temporale
            cmd = [
                str(quartus_sh),
                f'-t "{tcls}"/set_global_assignment.tcl',
                f'"{self.project_name}" "ENABLE_ADVANCED_IO_TIMING" "ON"'
            ]
            run_quartus(cmd)

        # Imposta il top level entity
        cmd = [
            str(quartus_sh),
            f'-t "{tcls}"/set_top_level_entity.tcl',
            f'"{self.project_name}" "{self.project_name}"'
        ]
        run_quartus(cmd, working_dir=self.project_dir)

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

    def program_device(self):
        """
        Programma il dispositivo usando il programmatore USB-Blaster
        """
        print("Programmazione del dispositivo...")

        # Cerca il programmatore USB-Blaster
        cmd = [
            str(self.quartus_bin / check_exe("quartus_pgm")),
            "-l"
        ]
        result = run_quartus(cmd, working_dir=self.project_dir)

        if "USB-Blaster" not in result:
            raise RuntimeError("USB-Blaster non trovato")

        # Programma il dispositivo
        sof_file = f"{self.project_name}.sof"
        cmd = [
            str(self.quartus_bin / check_exe("quartus_pgm")),
            "-c", "USB-Blaster",
            "-m", "JTAG",
            "-o", f"P;{sof_file}"
        ]
        run_quartus(cmd, working_dir=self.project_dir)


def main():
    global quartus_dir

    print("Usage: python main.py <quartus_dir> <board_name> [<verilog_file>]")
    if len(sys.argv) < 3 and False: # use default values
        sys.exit(1)

    verilog_files = [ # with example files
        r"""C:\Users\Riccardo Cecchini\Documents\DE0-Nano\DE0-Nano_v.1.2.8_SystemCD\Tools\DE0_Nano_SystemBuilder\CodeGenerated\DE0_NANO\DE0_NANO\DE0_NANO.v""",
        r"""C:\Users\Riccardo Cecchini\Documents\DE0-Nano\DE0-Nano_v.1.2.8_SystemCD\Tools\DE0_Nano_SystemBuilder\CodeGenerated\DE0_NANO\DE0_NANO\vjtag_interface.v"""
    ]

    arg_num = 1
    quartus_dir = sys.argv[arg_num] if len(sys.argv) > arg_num else 'C:\\altera\\13.1\\quartus'

    arg_num += 1
    board_name = sys.argv[arg_num] if len(sys.argv) > arg_num else 'de0_nano'

    arg_num += 1
    project_name = sys.argv[arg_num] if len(sys.argv) > arg_num else 'DE0_NANO'

    arg_num += 1
    if len(sys.argv) > arg_num:
        verilog_files.append(sys.argv[arg_num])

    try:
        automation = QuartusAutomation(quartus_dir, board_name, project_name)

        # Read the YAML file
        config = read_yaml_file("boards/"+board_name+".yaml")

        # Print the configuration
        print_quartus_config(config)

        # Crea e compila il progetto
        automation.create_project(verilog_files, device=config)
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
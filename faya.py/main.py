import os
import sys
import subprocess
import time
from pathlib import Path

from libs.yaml import *
from libs.debug import *
from libs.platform import *
from libs.paths import *

def check_exe(program):
    if is_windows():
        return program + '.exe'
    return program


def run(command: list, working_dir: str = None) -> str:
    """
    Run a Quartus command with proper environment setup and error handling.

    Args:
        command (list): Command and arguments as list
        working_dir (str): Working directory for the command
    """
    try:

        # Method 1: Using shell=True (Windows preferred)
        cmd_str = ' '.join(command)
        result = subprocess.run(
            cmd_str,
            shell=True,
            #env=os.environ.copy(), # shell or env
            #check=True,
            text=True,
            capture_output=True,
            cwd= working_dir
        )

        if len(result.stderr) > 0:
            raise RuntimeError(result.stderr)

        print("Command output:", result.stdout)
        return result.stdout

    except subprocess.CalledProcessError as e:
        print(f"Command failed with exit code {e.returncode}")
        print("Error output:", e.stderr)
        raise


class QuartusAutomation:
    def __init__(self, quartus_dir, board_name):
        """
        Inizializza l'automazione di Quartus

        Args:
            quartus_dir (str): Percorso della directory di installazione di Quartus
            board_name (str): Nome del progetto/top level entity
        """
        self.quartus_dir = Path(quartus_dir)

        self.project_name = board_name + "_proj"

        self.project_dir = './projects/' + self.project_name
        create_directory(self.project_dir)

        self.quartus_bin = self.quartus_dir / "bin64"

        # Verifica che la directory di Quartus esista
        if not self.quartus_dir.exists():
            raise FileNotFoundError(f"Directory Quartus non trovata: {self.quartus_dir}")

    def create_project(self, verilog_files, device_family="Cyclone V", device_part="5CSEMA5F31C6"):
        """
        Crea un nuovo progetto Quartus

        Args:
            verilog_files ([str]): Percorso del file Verilog
            device_family (str): Famiglia del dispositivo
            device_part (str): Codice parte del dispositivo
        """
        quartus_sh = self.quartus_bin / check_exe("quartus_sh")

        # Crea il progetto
        cmd = [
            str(quartus_sh),
            "--tcl_eval",
            f'project_new -overwrite -part {device_part} {self.project_name}'
        ]
        run(cmd, working_dir=self.project_dir)

        # Aggiungi il file Verilog
        for verilog_file in verilog_files:
            cmd = [
                str(quartus_sh),
                "--tcl_eval",
                f'set_global_assignment -name VERILOG_FILE {verilog_file}'
            ]
            run(cmd, working_dir=self.project_name)

        # Imposta il top level entity
        cmd = [
            str(quartus_sh),
            "--tcl_eval",
            f'set_global_assignment -name TOP_LEVEL_ENTITY {self.project_name}'
        ]
        run(cmd, working_dir=self.project_name)

    def compile_project(self):
        """
        Compila il progetto usando quartus_map, quartus_fit e quartus_asm
        """
        print("Iniziando la compilazione...")

        # Analysis & Synthesis
        run([
            str(self.quartus_bin / check_exe("quartus_map")),
            self.project_name
        ], working_dir=self.project_name)

        # Fitter
        run([
            str(self.quartus_bin / check_exe("quartus_fit")),
            self.project_name
        ], working_dir=self.project_name)

        # Assembler
        run([
            str(self.quartus_bin / check_exe("quartus_asm")),
            self.project_name
        ], working_dir=self.project_name)

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
        result = run(cmd, working_dir=self.project_name)

        if "USB-Blaster" not in result.stdout:
            raise RuntimeError("USB-Blaster non trovato")

        # Programma il dispositivo
        sof_file = f"{self.project_name}.sof"
        cmd = [
            str(self.quartus_bin / check_exe("quartus_pgm")),
            "-c", "USB-Blaster",
            "-m", "JTAG",
            "-o", f"P;{sof_file}"
        ]
        run(cmd, working_dir=self.project_name)


def main():
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
    if len(sys.argv) > arg_num:
        verilog_files.append(sys.argv[arg_num])

    try:
        automation = QuartusAutomation(quartus_dir, board_name)

        # Read the YAML file
        config = read_yaml_file("boards/"+board_name+".yaml")

        # Print the configuration
        print_quartus_config(config)

        # Crea e compila il progetto
        automation.create_project(verilog_files, device_family=config['board']['device_family'], device_part=config['board']['device'])
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
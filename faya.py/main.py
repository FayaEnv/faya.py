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


def run_quartus(command: list, working_dir: str = None) -> str:
    """
    Run a Quartus command with proper environment setup and error handling.

    Args:
        command (list): Command and arguments as list
        working_dir (str): Working directory for the command
    """
    try:

        # Method 1: Using shell=True (Windows preferred)
        cmds = command # just for debug purposes
        command = ' '.join(command)
        result = subprocess.run(
            command,
            shell=True,
            env=os.environ.copy(), # shell or env
            #check=True,
            text=True,
            capture_output=True,
            cwd= working_dir
        )

        out = result.stdout

        is_err = False if not('errors' in out and '0 errors' not in out) else True

        if len(result.stderr) > 0 or is_err:
            raise RuntimeError(result.stderr)

        print("Quartus output:", out)
        return out

    except subprocess.CalledProcessError as e:
        print(f"Command failed with exit code {e.returncode}")
        print("Error output:", e.stderr)
        raise


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

    def create_project(self, verilog_files, device=None):
        """
        Crea un nuovo progetto Quartus

        Args:
            verilog_files ([str]): Percorso del file Verilog
            device (object): Board device infos
        """

        if device is None:
            raise Exception("Device parameters mandatory")

        device_family = device['board']["device_family"]
        device_part = device['board']["device"]

        quartus_sh = self.quartus_bin / check_exe("quartus_sh")

        # Crea il progetto
        cmd = [
            str(quartus_sh),
            "--tcl_eval",
            f'project_new -overwrite -part {device_part} {self.project_name}'
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
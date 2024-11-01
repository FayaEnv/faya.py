import os
import sys
import subprocess
from pathlib import Path
import re

class QuartusIPInfo:
    def __init__(self, quartus_dir):
        """
        Inizializza la ricerca degli IP di Quartus

        Args:
            quartus_dir (str): Percorso della directory di installazione di Quartus
        """
        self.quartus_dir = Path(quartus_dir)
        self.quartus_bin = self.quartus_dir / "bin64"
        self.ip_dir = self.quartus_dir / "ip"

        if not self.quartus_dir.exists():
            raise FileNotFoundError(f"Directory Quartus non trovata: {self.quartus_dir}")

    def run_command(self, command, args):
        """
        Esegue un comando Quartus e attende il suo completamento

        Args:
            command (str): Nome del comando Quartus
            args (list): Lista di argomenti aggiuntivi
        Returns:
            subprocess.CompletedProcess: Risultato del comando
        """
        cmd = [str(self.quartus_bin / command), *args]
        print(f"Esecuzione comando: {' '.join(cmd)}")

        result = subprocess.run(cmd, capture_output=True, text=True)
        return result

    def find_megawizard_files(self):
        """
        Cerca tutti i file .mif nella directory di Quartus

        Returns:
            list: Lista di percorsi dei file .mif trovati
        """
        mif_files = []
        for root, dirs, files in os.walk(self.quartus_dir):
            for file in files:
                if file.endswith('.mif') or file.endswith('.tdf'):
                    mif_files.append(os.path.join(root, file))
        return mif_files

    def get_ip_files(self, ip_name):
        # Cerca nelle directory comuni degli IP
        ip_paths = [
            self.quartus_dir / "libraries" / "megafunctions",
            self.quartus_dir / "ip" / "altera",
            self.quartus_dir / "ip" / "altera_mf",
            self.quartus_dir / "ip"
        ]

        print(f"\nRicerca informazioni per IP: {ip_name}")
        found_files = []

        for ip_path in ip_paths:
            if ip_path.exists():
                for file in ip_path.rglob("*"):
                    if file.name.lower().startswith(ip_name.lower()):
                        if file.suffix in ['.tdf', '.v', '.vhd', '.mif']:
                            found_files.append(file)

        return found_files

    def get_ip_info(self, ip_name):
        """
        Cerca informazioni su uno specifico IP

        Args:
            ip_name (str): Nome dell'IP da cercare
        """
        found_files = self.get_ip_files(ip_name)

        if not found_files:
            print(f"Nessun file trovato per l'IP {ip_name}")
            return None

        print(f"\nFile trovati per {ip_name}:")
        for file in found_files:
            print(f"\nAnalisi file: {file}")
            try:
                with open(file, 'r') as f:
                    content = f.read()
                    # Cerca parametri e porte
                    self.analyze_file_content(content, file.suffix)
            except Exception as e:
                print(f"Errore nella lettura del file {file}: {e}")

    def analyze_file_content(self, content, file_type):
        """
        Analizza il contenuto di un file per estrarre informazioni sull'IP

        Args:
            content (str): Contenuto del file
            file_type (str): Tipo di file (.v, .tdf, etc.)
        """
        if file_type == '.v':
            self.analyze_verilog(content)
        elif file_type == '.tdf':
            self.analyze_tdf(content)
        elif file_type == '.vhd':
            self.analyze_vhdl(content)

    def analyze_verilog(self, content):
        """
        Analizza un file Verilog per estrarre parametri e porte
        """
        print("\nParametri trovati:")
        # Cerca definizioni di parametri
        import re
        param_pattern = r'parameter\s+(\w+)\s*=\s*([^;]+);'
        for match in re.finditer(param_pattern, content):
            print(f"  {match.group(1)} = {match.group(2)}")

        print("\nPorte trovate:")
        # Cerca definizioni di porte
        port_pattern = r'\b(input|output|inout)\s+(?:reg|wire)?\s*(?:\[[^\]]+\])?\s*(\w+)'
        for match in re.finditer(port_pattern, content):
            print(f"  {match.group(1)} {match.group(2)}")

    def analyze_tdf(self, content):
        """
        Analizza un file TDF per estrarre parametri e porte
        """
        print("\nParametri trovati:")
        param_pattern = r'PARAMETER\s*\("([^"]+)"\s*,\s*([^)]+)\)'
        for match in re.finditer(param_pattern, content, re.IGNORECASE):
            print(f"  {match.group(1)} = {match.group(2)}")

        print("\nPorte trovate:")
        port_pattern = r'\b(INPUT|OUTPUT|BIDIR)\s+(\w+)'
        for match in re.finditer(port_pattern, content, re.IGNORECASE):
            print(f"  {match.group(1).lower()} {match.group(2)}")

    def analyze_vhdl(self, content):
        """
        Analizza un file VHDL per estrarre parametri e porte
        """
        print("\nParametri trovati:")
        param_pattern = r'generic\s*\(\s*(\w+)\s*:\s*([^;]+);'
        for match in re.finditer(param_pattern, content, re.IGNORECASE):
            print(f"  {match.group(1)} : {match.group(2)}")

        print("\nPorte trovate:")
        port_pattern = r'\b(in|out|inout)\s+(\w+\s*:\s*[^;]+);'
        for match in re.finditer(port_pattern, content, re.IGNORECASE):
            print(f"  {match.group(1)} {match.group(2)}")


def main():
    quartus_dir = "C:\\altera\\13.1\\quartus"
    ip_name = "sld_virtual_jtag"

    try:
        ip_info = QuartusIPInfo(quartus_dir)
        ip_info.get_ip_info(ip_name)

    except Exception as e:
        print(f"\nErrore: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
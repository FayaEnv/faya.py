import os
import sys
import subprocess
from pathlib import Path
from .this_platform import *
from libs.this_platform import *

class QMegaWizManager:
    def __init__(self, quartus_dir):
        """
        Inizializza il gestore QMegaWiz

        Args:
            quartus_dir (str): Percorso della directory di installazione di Quartus
        """
        self.quartus_dir = Path(quartus_dir)
        self.quartus_bin = self.quartus_dir / "bin64"
        self.megawizard = self.quartus_bin / check_exe("qmegawiz")

        if not self.quartus_dir.exists():
            raise FileNotFoundError(f"Directory Quartus non trovata: {self.quartus_dir}")

        if not self.megawizard.exists():
            raise FileNotFoundError(f"QMegaWiz non trovato: {self.megawizard}")

    def list_available_megafunctions(self):
        """
        Lista le megafunctions disponibili usando qmegawiz
        """
        cmd = [str(self.megawizard), "--help"]
        print("Ricerca megafunctions disponibili...")

        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print("STDOUT:", result.stdout)
                print("STDERR:", result.stderr)
                raise subprocess.CalledProcessError(result.returncode, cmd)

            return result.stdout

        except subprocess.CalledProcessError as e:
            print(f"Errore nell'esecuzione di qmegawiz: {e}")
            return None

    def get_megafunction_info(self, megafunction_name):
        """
        Ottiene informazioni su una specifica megafunction

        Args:
            megafunction_name (str): Nome della megafunction
        """
        cmd = [str(self.megawizard), "-info", megafunction_name]
        print(f"\nRicerca informazioni per: {megafunction_name}")

        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print("STDOUT:", result.stdout)
                print("STDERR:", result.stderr)
                raise subprocess.CalledProcessError(result.returncode, cmd)

            return result.stdout

        except subprocess.CalledProcessError as e:
            print(f"Errore nel recupero delle informazioni: {e}")
            return None


def main():
    if len(sys.argv) < 2:
        print("Uso: python script.py <quartus_dir> [megafunction_name]")
        print("Esempi:")
        print("  Lista tutte le megafunctions:")
        print("    python script.py C:/altera/13.1/quartus")
        print("  Informazioni su una megafunction specifica:")
        print("    python script.py C:/altera/13.1/quartus altsource_probe")
        sys.exit(1)

    quartus_dir = sys.argv[1]
    megafunction_name = sys.argv[2] if len(sys.argv) > 2 else None

    try:
        manager = QMegaWizManager(quartus_dir)

        if megafunction_name:
            # Mostra informazioni sulla megafunction specifica
            info = manager.get_megafunction_info(megafunction_name)
            if info:
                print("\nInformazioni trovate:")
                print(info)
        else:
            # Lista tutte le megafunctions disponibili
            megafunctions = manager.list_available_megafunctions()
            if megafunctions:
                print("\nMegafunctions disponibili:")
                print(megafunctions)

    except Exception as e:
        print(f"\nErrore: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
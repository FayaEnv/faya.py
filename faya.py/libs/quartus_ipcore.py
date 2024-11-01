import re
import xml.etree.ElementTree as ET


def get_ip_tool_version(ip_file_path):
    """
    Estrae l'IP_TOOL_VERSION da un file IP di Quartus.

    Args:
        ip_file_path (str): Percorso del file IP (.ip o .qsys)

    Returns:
        str: La versione dell'IP tool, o None se non trovata
    """
    try:
        # Prova prima con parsing XML (per file .ip)
        try:
            tree = ET.parse(ip_file_path)
            root = tree.getroot()

            # Cerca il tag con IP_TOOL_VERSION
            for elem in root.iter():
                if 'IP_TOOL_VERSION' in elem.attrib:
                    return elem.attrib['IP_TOOL_VERSION']

        except ET.ParseError:
            # Se non è XML valido, prova con ricerca nel testo
            with open(ip_file_path, 'r') as file:
                content = file.read()

                # Cerca il pattern IP_TOOL_VERSION
                match = re.search(r'IP_TOOL_VERSION\s*=\s*"([^"]+)"', content)
                if match:
                    return match.group(1)

        return None

    except Exception as e:
        print(f"Errore durante la lettura del file: {str(e)}")
        return None


# Esempio di utilizzo
def main():
    ip_file = "esempio.ip"  # Sostituire con il percorso del tuo file IP
    version = get_ip_tool_version(ip_file)

    if version:
        print(f"IP Tool Version: {version}")
    else:
        print("Versione non trovata")


if __name__ == "__main__":
    main()
# First, make sure you have installed pyyaml correctly
# pip install pyyaml

import sys
from ruamel.yaml import YAML, YAMLError  # Alternative to PyYAML
# or if you prefer PyYAML:
# import yaml as pyyaml  # Renaming to avoid confusion

from typing import Dict, Any


def read_yaml_file(file_path: str) -> Dict[str, Any]:
    """
    Read and parse a YAML file.

    Args:
        file_path (str): Path to the YAML file

    Returns:
        dict: Parsed YAML content

    Raises:
        FileNotFoundError: If the file doesn't exist
        YAMLError: If the YAML is invalid
    """
    yaml = YAML(typ='safe')  # Create a YAML parser instance

    try:
        with open(file_path, 'r') as file:
            return yaml.load(file)
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        sys.exit(1)
    except YAMLError as e:
        print(f"Error parsing YAML file: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)


def print_quartus_config(config: Dict[str, Any]) -> None:
    """
    Print the parsed Quartus configuration in a readable format.

    Args:
        config (dict): Parsed YAML configuration
    """
    # Print project information
    print("\n=== Project Information ===")
    for key, value in config['project'].items():
        print(f"{key}: {value}")

    # Print pin assignments
    print("\n=== Pin Assignments ===")
    for interface, pins in config['pins'].items():
        print(f"\n{interface.upper()}:")
        for pin in pins:
            print(f"  {pin['signal']}: {pin['pin']} ({pin['io_standard']})")


def main():
    # Example usage
    yaml_file = "../boards/de0_nano.yaml"

    try:
        # Read the YAML file
        config = read_yaml_file(yaml_file)

        # Print the configuration
        print_quartus_config(config)

    except KeyError as e:
        print(f"Error: Missing expected key in YAML file: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
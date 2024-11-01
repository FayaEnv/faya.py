import os
import sys
from pathlib import Path
from typing import Union, Optional


def create_directory(path: Union[str, Path], *, parents: bool = True, exist_ok: bool = True) -> Optional[Path]:
    """
    Create a directory at the specified path if it doesn't exist.

    Args:
        path (Union[str, Path]): The path where the directory should be created
        parents (bool): If True, create parent directories if they don't exist
        exist_ok (bool): If True, don't raise an error if directory exists

    Returns:
        Path: Path object of the created directory if successful, None if failed

    Raises:
        FileExistsError: If directory exists and exist_ok is False
        PermissionError: If user lacks permission to create directory
    """
    try:
        # Convert string path to Path object
        directory = Path(path)

        # Resolve path to absolute path, eliminating any '..' or '.'
        directory = directory.resolve()

        # Create directory with specified parameters
        directory.mkdir(parents=parents, exist_ok=exist_ok)

        print(f"Successfully created directory: {directory}")
        return directory

    except FileExistsError:
        print(f"Directory already exists: {path}")
        raise
    except PermissionError:
        print(f"Permission denied to create directory: {path}")
        return None
    except OSError as e:
        print(f"Failed to create directory: {path}")
        print(f"Error: {e}")
        return None


def create_directory_safe(base_path: Union[str, Path], *subdirs: str) -> Optional[Path]:
    """
    Safely create a directory structure under a base path.

    Args:
        base_path (Union[str, Path]): The base directory path
        *subdirs (str): Variable number of subdirectory names

    Returns:
        Path: Path object of the created directory if successful, None if failed

    Example:
        create_directory_safe('/tmp', 'project', 'data', 'raw')
        # Creates /tmp/project/data/raw
    """
    try:
        # Convert base path to absolute path
        full_path = Path(base_path).resolve()

        # Add subdirectories to path
        for subdir in subdirs:
            # Remove any potentially dangerous characters
            safe_subdir = "".join(c for c in subdir if c.isalnum() or c in "._- ")
            full_path = full_path / safe_subdir

        # Create the directory
        return create_directory(full_path)

    except Exception as e:
        print(f"Error creating directory structure: {e}")
        return None


def get_faya_path() -> str:
    script_path = Path(__file__).resolve()
    return script_path.parent.parent

def example_usage():
    """Example usage of directory creation functions"""

    # Basic directory creation
    create_directory("./data")

    # Create nested directories
    create_directory("./projects/python/data")

    # Using Path object
    path = Path.home() / "documents" / "projects"
    create_directory(path)

    # Create directory structure safely
    create_directory_safe("./projects", "python", "data", "raw")

    # Example with error handling
    try:
        # Try to create directory without parents (will fail if parents don't exist)
        create_directory("./a/b/c", parents=False)
    except Exception as e:
        print(f"Failed to create directory: {e}")

    # Create temporary project structure
    project_dirs = [
        "src",
        "tests",
        "docs",
        "data/raw",
        "data/processed",
        "models",
        "configs"
    ]

    for dir_path in project_dirs:
        create_directory(f"./project/{dir_path}")


if __name__ == "__main__":
    example_usage()
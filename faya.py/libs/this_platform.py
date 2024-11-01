import sys
import os
import platform


def is_windows() -> bool:
    """
    Simple check if running on Windows using sys.platform
    """
    return sys.platform.startswith('win')


def get_os_info() -> dict:
    """
    Get detailed information about the operating system
    Returns a dictionary with OS-related information
    """
    os_info = {
        'is_windows': False,
        'platform': sys.platform,
        'os_name': os.name,
        'platform_system': platform.system(),
        'platform_release': platform.release(),
        'platform_version': platform.version(),
        'platform_machine': platform.machine(),
        'platform_processor': platform.processor(),
        'platform_architecture': platform.architecture(),
        'path_separator': os.path.sep,
        'line_separator': os.linesep,
        'env_paths': os.environ.get('PATH', '').split(os.pathsep)
    }

    # Check using different methods
    os_info['is_windows'] = any([
        sys.platform.startswith('win'),
        os.name == 'nt',
        platform.system() == 'Windows'
    ])

    return os_info


def get_windows_specific_info() -> dict:
    """
    Get Windows-specific information (only works on Windows)
    """
    if not is_windows():
        return {'error': 'Not running on Windows'}

    try:
        import winreg
        windows_info = {
            'windows_version': sys.getwindowsversion(),
            'system_root': os.environ.get('SYSTEMROOT', ''),
            'program_files': os.environ.get('PROGRAMFILES', ''),
            'program_files_x86': os.environ.get('PROGRAMFILES(X86)', ''),
            'app_data': os.environ.get('APPDATA', ''),
            'local_app_data': os.environ.get('LOCALAPPDATA', ''),
            'user_profile': os.environ.get('USERPROFILE', ''),
            'home_drive': os.environ.get('HOMEDRIVE', ''),
            'home_path': os.environ.get('HOMEPATH', '')
        }

        # Try to get Windows edition from registry
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                r"SOFTWARE\Microsoft\Windows NT\CurrentVersion") as key:
                windows_info['product_name'] = winreg.QueryValueEx(key, "ProductName")[0]
                windows_info['build_number'] = winreg.QueryValueEx(key, "CurrentBuildNumber")[0]
        except Exception:
            pass

        return windows_info
    except Exception as e:
        return {'error': f'Error getting Windows info: {str(e)}'}

def check_exe(program):
    if is_windows():
        return program + '.exe'
    return program

def example_usage():
    """
    Example of how to use the OS detection in practice
    """
    # Basic check
    if is_windows():
        print("Running on Windows")
        # Windows-specific code
        path = "C:\\Users\\example"
    else:
        print("Running on non-Windows OS")
        # Unix-style path
        path = "/home/example"

    # Get detailed OS information
    os_info = get_os_info()

    print("\nOS Information:")
    print(f"Platform: {os_info['platform']}")
    print(f"OS Name: {os_info['os_name']}")
    print(f"System: {os_info['platform_system']}")
    print(f"Release: {os_info['platform_release']}")
    print(f"Architecture: {os_info['platform_architecture']}")

    # If on Windows, get Windows-specific information
    if os_info['is_windows']:
        windows_info = get_windows_specific_info()
        if 'error' not in windows_info:
            print("\nWindows Specific Information:")
            print(f"Windows Version: {windows_info['windows_version']}")
            print(f"System Root: {windows_info['system_root']}")
            print(f"Program Files: {windows_info['program_files']}")
            if 'product_name' in windows_info:
                print(f"Windows Edition: {windows_info['product_name']}")

    # Example of OS-specific path handling
    def get_app_data_path():
        if is_windows():
            return os.environ.get('APPDATA', '')
        else:
            return os.path.expanduser('~/.config')

    print(f"\nApp Data Path: {get_app_data_path()}")


if __name__ == "__main__":
    example_usage()
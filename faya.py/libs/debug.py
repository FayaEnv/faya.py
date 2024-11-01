import sys
import os
import inspect


def is_debug_mode() -> bool:
    """
    Comprehensive check for debug mode using multiple methods.
    Returns True if any debug condition is met.
    """
    # Method 1: Check for common debugger traces
    gettrace = getattr(sys, 'gettrace', None)
    if gettrace is not None and gettrace():
        return True

    # Method 2: Check for specific debuggers
    debuggers = {
        'pydev': 'PYDEVD_USE_FRAME_EVAL',  # PyCharm
        'vscode': 'DEBUGPY_VERSION',  # VS Code
        'pytest': 'PYTEST_CURRENT_TEST',  # PyTest
        'ipython': 'IPY_INTERRUPT_EVENT',  # IPython/Jupyter
    }

    for env_var in debuggers.values():
        if os.getenv(env_var) is not None:
            return True

    # Method 3: Check for -d or --debug CLI argument
    if '--debug' in sys.argv or '-d' in sys.argv:
        return True

    # Method 4: Check current stack frames for debugger signatures
    for frame in inspect.stack():
        if 'pydevd' in frame.filename or 'debugpy' in frame.filename:
            return True

    return False


def get_debug_info() -> dict:
    """
    Get detailed information about the current debug state.
    Returns a dictionary with debug-related information.
    """
    debug_info = {
        'is_debug': False,
        'debugger_type': None,
        'debug_env_vars': [],
        'cli_args': [],
        'stack_info': []
    }

    # Check trace function
    gettrace = getattr(sys, 'gettrace', None)
    if gettrace is not None and gettrace():
        debug_info['is_debug'] = True
        debug_info['debugger_type'] = 'trace_function'

    # Check environment variables
    debug_env_vars = {
        'PYDEVD_USE_FRAME_EVAL': 'PyCharm',
        'DEBUGPY_VERSION': 'VS Code',
        'PYTEST_CURRENT_TEST': 'PyTest',
        'IPY_INTERRUPT_EVENT': 'IPython/Jupyter'
    }

    for env_var, debugger in debug_env_vars.items():
        if os.getenv(env_var) is not None:
            debug_info['is_debug'] = True
            debug_info['debugger_type'] = debugger
            debug_info['debug_env_vars'].append(env_var)

    # Check CLI arguments
    debug_args = ['--debug', '-d']
    for arg in debug_args:
        if arg in sys.argv:
            debug_info['is_debug'] = True
            debug_info['cli_args'].append(arg)

    # Check stack frames
    for frame in inspect.stack():
        if any(debugger in frame.filename
               for debugger in ['pydevd', 'debugpy', 'pdb']):
            debug_info['is_debug'] = True
            debug_info['stack_info'].append(frame.filename)

    return debug_info


def main():
    """Example usage of debug detection"""
    # Basic check
    if is_debug_mode():
        print("Script is running in debug mode")
    else:
        print("Script is running normally")

    # Detailed debug info
    debug_info = get_debug_info()
    print("\nDetailed Debug Information:")
    print(f"Is Debug Mode: {debug_info['is_debug']}")
    print(f"Debugger Type: {debug_info['debugger_type']}")
    if debug_info['debug_env_vars']:
        print("Debug Environment Variables:", debug_info['debug_env_vars'])
    if debug_info['cli_args']:
        print("Debug CLI Arguments:", debug_info['cli_args'])
    if debug_info['stack_info']:
        print("Debugger Stack Information:", debug_info['stack_info'])


if __name__ == "__main__":
    main()
import subprocess
import platform
from typing import List


def run(args: List[str]) -> subprocess.CompletedProcess[str]:
    """
    Runs a subprocess with the specified arguments, always capturing stdout and stderr,
    and using UTF-8 encoding for text.

    :param args: The command to run and its arguments.
    :type args: List[str]
    :return: The result of the subprocess.
    :rtype: subprocess.CompletedProcess[str]
    """
    kwargs = {
        'check': True,
        'text': True,
        'encoding': 'utf-8',
        'stdout': subprocess.PIPE,
        'stderr': subprocess.PIPE
    }

    if platform.system() == 'Windows':
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        kwargs['startupinfo'] = si

    return subprocess.run(args, **kwargs)
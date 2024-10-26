import subprocess
import platform
import html
import re

import nh3


def run(args: list[str]) -> subprocess.CompletedProcess[str]:
    """
    Runs a subprocess with the specified arguments, always capturing stdout and stderr,
    and using UTF-8 encoding for text. On Windows, the subprocess is run with a hidden window.

    :param args: The command to run and its arguments.
    :type args: list[str]
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


def cleanText(text: str) -> str:
    """
    Clean the input text by unescaping HTML entities, normalizing fractions and temperatures,
    collapsing whitespace, and stripping leading and trailing spaces.

    Args:
        text (str): The input text to be cleaned.

    Returns:
        str: The cleaned text.
    """
    if text:
        text = stripHtml(text)
        text = html.unescape(text)
        text = collapseWhitespace(text)
        text = text.strip()
    return text


def stripHtml(text: str) -> str:
    """
    Strip all HTML tags from the input text using nh3, allowing no tags.

    Args:
        text (str): The input text with potential HTML content.

    Returns:
        str: The text with HTML tags removed.
    """
    return nh3.clean(text, tags=set())


def collapseWhitespace(val: str) -> str:
    """
    Replace various whitespace characters (newlines, tabs, etc.) with a space, and collapse multiple
    spaces into a single space.

    Args:
        val (str): The input text with potential excessive whitespace.

    Returns:
        str: The text with collapsed whitespace.
    """
    val = re.sub(r'[\n\r\u200B\t\xA0\s]', ' ', val)
    val = re.sub(r'\s{2,}', ' ', val)
    val = val.strip()
    return val
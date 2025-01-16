import subprocess
import platform
import html
import re

import nh3


def run(args: list[str]) -> subprocess.CompletedProcess[str]:
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


def clean_text(text: str) -> str:
    if text:
        text = strip_html(text)
        text = html.unescape(text)
        text = collapse_whitespace(text)
        text = text.strip()
    return text


def strip_html(text: str) -> str:
    return nh3.clean(text, tags=set())


def collapse_whitespace(val: str) -> str:
    val = re.sub(r'[\n\r\u200B\t\xA0\s]', ' ', val)
    val = re.sub(r'\s{2,}', ' ', val)
    val = val.strip()
    return val

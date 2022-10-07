import math
import random
import re

try:
    import ujson as json  # Speedup if present; no big deal if not
except ImportError:
    import json


def remove_comments(json_like):
    comments_re = re.compile(
        r'//.*?$|/\*.*?\*/|\'(?:\\.|[^\\\'])*\'|"(?:\\.|[^\\"])*"',
        re.DOTALL | re.MULTILINE
    )

    def replacer(match):
        s = match.group(0)
        if s[0] == '/':
            return ""
        return s

    return comments_re.sub(replacer, json_like)


def remove_trailing_commas(json_like):
    trailing_object_commas_re = re.compile(
        r'(,)\s*}(?=([^"\\]*(\\.|"([^"\\]*\\.)*[^"\\]*"))*[^"]*$)')
    trailing_array_commas_re = re.compile(
        r'(,)\s*\](?=([^"\\]*(\\.|"([^"\\]*\\.)*[^"\\]*"))*[^"]*$)')
    # Fix objects {} first
    objects_fixed = trailing_object_commas_re.sub("}", json_like)
    # Now fix arrays/lists [] and return the result
    return trailing_array_commas_re.sub("]", objects_fixed)


PERSISTENT_ID_CHARS = '0123456789abcdef'
PERSISTENT_ID_DASHS = [8, 12, 16, 20]


def create_persistent_id():
    r = ''
    for i in range(32):
        if i in PERSISTENT_ID_DASHS:
            r += '-'
        r += PERSISTENT_ID_CHARS[math.floor(random.random() * len(PERSISTENT_ID_CHARS))]
    return r


class Jbeam:
    def __init__(self, lines=None):
        if lines is None:
            lines = []
        self.lines = lines

    def tostring(self, indent=None):
        return '\n'.join([json.dumps(line, indent=indent) for line in self.lines])


def load(s: str):
    s = remove_comments(s)
    s = remove_trailing_commas(s)
    try:
        return Jbeam([json.loads(s)])
    except json.JSONDecodeError:
        pass
    return Jbeam([json.loads(line) for line in s.splitlines(False)])


if __name__ == '__main__':
    print(create_persistent_id())

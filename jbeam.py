import json
import math
import random


class JSONWithCommentsDecoder(json.JSONDecoder):
    def __init__(self, **kw):
        super().__init__(**kw)

    def decode(self, s):
        s = '\n'.join(l for l in s.split('\n') if not l.lstrip(' ').startswith('//'))
        return super().decode(s)


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

    def tostring(self):
        return '\n'.join([json.dumps(line) for line in self.lines])


def load(s: str):
    try:
        return Jbeam([json.loads(s, cls=JSONWithCommentsDecoder)])
    except json.JSONDecodeError:
        pass
    return Jbeam([json.loads(line, cls=JSONWithCommentsDecoder) for line in s.splitlines(False)])


if __name__ == '__main__':
    print(create_persistent_id())

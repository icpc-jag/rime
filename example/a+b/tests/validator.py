#!/usr/bin/python

import re
import sys

MAX = 1000000000


def main():
    m = re.match(r'^(\d+) (\d+)\n$', sys.stdin.read())
    assert m, 'Does not match with regexp'
    a, b = map(int, m.groups())
    assert 0 <= a <= MAX, 'a out of range: %d' % a
    assert 0 <= b <= MAX, 'a out of range: %d' % b


if __name__ == '__main__':
    main()

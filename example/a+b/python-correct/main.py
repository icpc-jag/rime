#!/usr/bin/python

import sys


def main():
    a, b = map(int, sys.stdin.read().strip().split())
    print(a + b)


if __name__ == '__main__':
    main()

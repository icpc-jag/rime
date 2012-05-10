#!/usr/bin/python

import random

MAX = 1000000000
seq = 0

def Generate(a, b):
  global seq
  filename = '50-random%02d.in' % seq
  with open(filename, 'w') as f:
    print >>f, a, b
  seq += 1

def main():
  for _ in xrange(20):
    Generate(random.randrange(0, MAX), random.randrange(0, MAX))
 
if __name__ == '__main__':
  main()

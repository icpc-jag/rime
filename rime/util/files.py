#!/usr/bin/python
#
# Copyright (c) 2011 Rime Project.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#


from __future__ import with_statement
import datetime
import shutil
import os
import os.path
import pickle
import platform
import subprocess


_devnull = open(os.devnull, 'r+')


def CopyFile(src, dst):
  shutil.copy(src, dst)

def MakeDir(dir):
  if not os.path.isdir(dir):
    os.makedirs(dir)

def CopyTree(src, dst):
  MakeDir(dst)
  files = ListDir(src, True)
  for f in files:
    srcpath = os.path.join(src, f)
    dstpath = os.path.join(dst, f)
    if os.path.isdir(srcpath):
      MakeDir(dstpath)
    else:
      CopyFile(srcpath, dstpath)

def RemoveTree(dir):
  if os.path.exists(dir):
    shutil.rmtree(dir)

def GetModified(file):
  try:
    return datetime.datetime.fromtimestamp(os.path.getmtime(file))
  except:
    return datetime.datetime.min

def GetLastModifiedUnder(dir):
  return max([GetModified(os.path.join(dir, name))
              for name in (ListDir(dir, True) + [dir])])

def CreateEmptyFile(file):
  open(file, 'w').close()

def ListDir(dir, recursive=False):
  files = []
  try:
    files = filter(lambda x: not x.startswith('.'),
                   os.listdir(dir))
    if recursive:
      for subfile in files[:]:
        subdir = os.path.join(dir, subfile)
        if os.path.isdir(subdir):
          files += [os.path.join(subfile, s)
                    for s in ListDir(subdir, True)]
  except:
    pass
  return files

def PickleSave(obj, file):
  with open(file, 'w') as f:
    pickle.dump(obj, f)

def PickleLoad(file):
  with open(file, 'r') as f:
    obj = pickle.load(f)
    return obj

def ConvPath(path):
  if not platform.uname()[0].lower().startswith('cygwin'):
    return path
  try:
    p = subprocess.Popen(['cygpath', '-wp', path], stdout=subprocess.PIPE)
    newpath = p.communicate()[0].rstrip('\r\n')
    if p.returncode == 0:
      return newpath
  except:
    pass
  return path

def LocateBinary(name):
  if 'PATH' in os.environ:
    paths = os.environ['PATH']
  else:
    paths = os.defpath
  for path in paths.split(os.pathsep):
    bin = os.path.join(path, name)
    if os.path.isfile(bin) and os.access(bin, os.X_OK):
      return bin
  return None

def OpenNull():
  return _devnull

def ReadFile(name):
  try:
    with open(name, 'r') as f:
      return f.read()
  except:
    return None

def WriteFile(content, name):
  try:
    with open(name, 'w') as f:
      f.write(content)
    return True
  except:
    return False

def AppendFile(content, name):
  try:
    with open(name, 'a') as f:
      f.write(content)
      return True
  except:
    return False

# -*- coding: utf-8 -*-
import glob, os
import fnmatch
import os

matches = []
for root, dirnames, filenames in os.walk(os.path.join('icons', 'default')):
  for filename in fnmatch.filter(filenames, '*.*g'):
      matches.append((root, filename))
f = open("resources.qrc", "w")
f.write("<RCC>\n")
f.write("    <qresource>\n")
for root,name in matches:
    f.write('        <file alias="%s">%s</file>\n' % (name,os.path.join(root,name)))
f.write("    </qresource>\n")
f.write("</RCC>\n")
f.close()
os.system("pyrcc4 resources.qrc > resources.py")
 

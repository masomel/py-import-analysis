import os
import sys

from collections import OrderedDict

def collect_lib_depth(lib):
    os.system("sfood --depth "+"libs/"+lib+" > "+OUTPUT_DIR+"/"+lib+"-lib-depth")

OUTPUT_DIR = "data/depths/libs"

os.system("mkdir -p "+OUTPUT_DIR)

libfile = open("data/top50-libs.txt", "r")
lib_list = [l.strip() for l in libfile.readlines()]
libfile.close()

num_libs = 0
for l in lib_list:
    if not l.startswith('.'):
        print("--- current app: "+l)
        collect_lib_depth(l)
        num_libs += 1

print("Number of libs being scraped: "+str(num_libs))

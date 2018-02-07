# Given a set of apps under a certain category,
# this scrapes them for all imported libraries and
# sanitizes the result to obtain a list of all
# imported third-party libraries (a first-party library is a module
# that is part of the app that is imported)

import os
import sys

from collections import OrderedDict

def collect_imports(app):
    os.system("sfood-imports --unified "+APP_PATH+"/"+app+" > "+RAW_DATA_DIR+"/"+app+"-imports")

def collect_unused(app):
    os.system("sfood-checker "+APP_PATH+"/"+app+" > "+RAW_DATA_DIR+"/"+app+"-unused")

def collect_deps(app):
    os.system("sfood "+APP_PATH+"/"+app+" > "+RAW_DATA_DIR+"/"+app+"-deps")

def aggregate_set(cat, s):
    set_files = os.listdir(RAW_DATA_DIR)

    agg = []
    for f in set_files:
        if f.endswith("-"+s):
            with open(RAW_DATA_DIR+"/"+f, "r") as ifile:
                agg.extend([i for i in ifile])

    aggfile = open(RAW_DATA_DIR+"/"+cat+"-"+s+".txt", "w+")
    agg.sort()
    for i in agg:
        aggfile.write(i)
    aggfile.close()
    
# pass in the category: visual, audio or env
cat = sys.argv[1]

APP_DIR = "../apps"
RAW_DATA_DIR = "raw/imports/"+cat

# expect apps to be located in apps/cat/
APP_PATH = APP_DIR+"/"+cat

# let's organize our imports by app
app_list = os.listdir(APP_PATH)

os.system("mkdir -p "+RAW_DATA_DIR)

num_apps = 0
# iterate through all apps to organize the imports
for a in app_list:
    if not a.startswith('.'):
        print("--- current app: "+a)
        collect_imports(a)
        collect_unused(a)
        collect_deps(a)
        num_apps += 1

print("Number of "+cat+" apps being scraped: "+str(num_apps))

aggregate_set(cat, "imports")
aggregate_set(cat, "unused")
aggregate_set(cat, "deps")

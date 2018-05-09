# Given a set of apps under a certain category,
# this scrapes them for all imported libraries and
# sanitizes the result to obtain a list of all
# imported third-party libraries (a first-party library is a module
# that is part of the app that is imported)

import os
import sys

from collections import OrderedDict

def collect_imports(app):
    os.system("sfood --extract-imports "+APP_PATH+"/"+app+" > "+OUTPUT_DIR+"/"+app+"-imports")

# pass in the category: visual, audio or env
cat = sys.argv[1]

APP_DIR = "../apps"
OUTPUT_DIR = "data/imports/"+cat

# expect apps to be located in apps/cat/
APP_PATH = APP_DIR+"/"+cat

# let's organize our imports by app
app_list = os.listdir(APP_PATH)

os.system("mkdir -p "+OUTPUT_DIR)

num_apps = 0
# iterate through all apps to organize the imports
for a in app_list:
    if not a.startswith('.'):
        print("--- current app: "+a)
        collect_imports(a)
        num_apps += 1

print("Number of "+cat+" apps being scraped: "+str(num_apps))

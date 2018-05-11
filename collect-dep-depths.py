

import os
import sys

from collections import OrderedDict

def collect_depth(app):
    os.system("sfood --depth "+APP_PATH+"/"+app+" > "+OUTPUT_DIR+"/"+app+"-depth")

# pass in the category: visual, audio or env
cat = sys.argv[1]

APP_DIR = "../apps"
OUTPUT_DIR = "data/depths/"+cat

# expect apps to be located in apps/cat/
APP_PATH = APP_DIR+"/"+cat

# let's organize our depths by app
app_list = os.listdir(APP_PATH)

os.system("mkdir -p "+OUTPUT_DIR)

num_apps = 0
# iterate through all apps to collect the depths
for a in app_list:
    if not a.startswith('.'):
        print("--- current app: "+a)
        collect_depth(a)
        num_apps += 1

print("Number of "+cat+" apps being scraped: "+str(num_apps))

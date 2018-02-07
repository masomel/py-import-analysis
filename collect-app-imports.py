# Given a set of apps under a certain category,
# this scrapes them for all imported libraries and
# sanitizes the result to obtain a list of all
# imported third-party libraries (a first-party library is a module
# that is part of the app that is imported)

import os
import sys

from collections import OrderedDict

APP_DIR = "../py-iot-apps"
RAW_DATA_DIR = "raw"

# pass in the category: visual, audio or env
cat = sys.argv[1]

# expect apps to be located in apps/cat/
app_path = APP_DIR+"/"+cat+"/"

# let's organize our imports by app
app_list = os.listdir(app_path)

apps = OrderedDict()
for a in app_list:
    if not a.startswith('.'):
        app = app_path+a
        apps[app] = OrderedDict()

print("Number of "+cat+" apps being scraped: "+str(len(apps)))

# iterate through all apps to organize the imports
for a in apps:
    print("--- current app: "+a)
    os.system("sfood-imports --unified "+a+" > "+RAW_DATA_DIR+"/imports/"+cat+"/"+a+"-imports")
    os.system("sfood -ii -u "+a+" > "+RAW_DATA_DIR+"/imports/"+cat+"/"+a+"-deps")

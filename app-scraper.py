# Given a set of apps under a certain category,
# this scrapes them for all imported libraries and
# sanitizes the result to obtain a list of all
# imported third-party libraries (a first-party library is a module
# that is part of the app that is imported)

import os
import sys

from collections import OrderedDict

from util import *
from import_scraper import *

APP_DIR = "../apps"
RAW_DATA_DIR = "raw"

# pass in the category: visual, audio or env
cat = sys.argv[1]

# expect apps to be located in apps/cat/
app_path = APP_DIR+"/"+cat+"/"

imports_raw, unused_raw = extract_imports(cat, app_path)

# let's organize our imports by app
app_list = os.listdir(app_path)

apps = OrderedDict()
for a in app_list:
    if not a.startswith('.'):
        app = app_path+a
        apps[app] = OrderedDict()

print("Number of "+cat+" apps being scraped: "+str(len(apps)))

call_to_native = OrderedDict()
hybrid = OrderedDict()
# iterate through all apps to organize the imports
for a in apps:
    print("--- current app: "+a)
    proc_srcs = []
    hybrid_srcs = []

    # group the raw unused by app
    print("Grouping all unused by app")
    apps[a]['unused'] = group_by(a, unused_raw)

    # group the raw imports by app
    print("Grouping all imports by app")
    apps[a]['raw_imports'] = group_by(a, imports_raw)

    # iterate over the raw_imports to replace any pkg-level imports in
    # any "unused" __init__.py files
    if not a.endswith(".py"):
        apps[a]['raw_imports'] = replace_unused_init_imports(apps[a]['raw_imports'], apps[a]['unused'], a)

    # iterate over the raw_imports to collect the ones that call native code/use ctypes
    print("Checking if app calls a native process is hybrid python-C")
    shlibs = {}
    for src, i in apps[a]['raw_imports'].items():
        calls = []
        loads = []
        shlibs[src] = []
        for l in i:
            if l == "os" or l == "subprocess" or l == "subprocess.call" or l == "subprocess.Popen":
                c = scan_source_native(src)
                if len(c) > 0:
                    calls.extend(c)
            elif l == "ctypes":
                lds = scan_source_ctypes(src)
                if len(lds) > 0:
                    loads.extend(lds)
            elif not a.endswith(".py"):
                lds = search_shared_libs(a, l)
                if len(lds) > 0:
                    loads.extend(lds)
                    shlibs[src].append(l)
        if len(calls) > 0:
            proc_srcs.append({src:calls})
        if len(loads) > 0:
            hybrid_srcs.append({src:loads})

    # let's remove any raw imports that actually are shared libs
    for src, sh in shlibs.items():
        for s in sh:
            apps[a]['raw_imports'][src].remove(s)

    if len(proc_srcs) > 0:
        call_to_native[a] = proc_srcs

    if len(hybrid_srcs) > 0:
        hybrid[a] = hybrid_srcs

    # iterate over each source file's imports to find
    # the first-party imports
    if not a.endswith(".py"):
        # make sure to sort the sources to have a deterministic analysis
        apps[a]['raw_imports'] = OrderedDict(sorted(apps[a]['raw_imports'].items(), key=lambda t: t[0]))

        apps[a]['imports'] = replace_fp_mod_group(apps[a], a, 'raw_imports')
    else:
        # we can do this since the app name is the only source file in the raw imports
        apps[a]['imports'] = apps[a]['raw_imports'][a]

    # we only want to store the pkg names
    apps[a]['imports'] = get_pkg_names(apps[a], 'imports')

    # we're no longer removing stdlib imports bc this will be done as part of the
    # analysis
    # apps[a]['imports'] = remove_stdlib_imports(apps[a]['imports'])
                                               
    # iterate of each source's files imports to remove unused imports that actually appear
    # in the list of imports
    if not a.endswith(".py"):
        # make sure to sort the sources to have a deterministic analysis
        apps[a]['unused'] = OrderedDict(sorted(apps[a]['unused'].items(), key=lambda t: t[0]))

        apps[a]['unused'] = replace_fp_mod_group(apps[a], a, 'unused')
    else:
        # we can do this since the app name is the only source file in the raw imports
        apps[a]['unused'] = apps[a]['unused'][a]

    # remove the raw imports once we're done with all the parsing
    del apps[a]['raw_imports']

    # now we only want to store the pkg names
    apps[a]['unused'] = get_pkg_names(apps[a], 'unused')

    # if a pkg is under unused (possibly bc an app submodule doesn't
    # use it or some submodule is unused), but it also appears in imports
    # consider it used by the app, so remove it from unused
    pruned_unused = []
    for l in apps[a]['unused']:
        if l not in apps[a]['imports']:
            pruned_unused.append(l)

    apps[a]['unused'] = pruned_unused

write_map(call_to_native, RAW_DATA_DIR+"/"+cat+"-call-native.txt", perm="w+", sort=True)
write_map(hybrid, RAW_DATA_DIR+"/"+cat+"-hybrid-apps.txt", perm="w+", sort=True)

li = []
for a in apps:
    for i in sorted(apps[a]['imports']):
        li.append(i)

write_list_raw(li, RAW_DATA_DIR+"/"+cat+"-libs.txt")

li = []
for a in apps:
    for i in sorted(apps[a]['unused']):
        li.append(i)

write_list_raw(li, RAW_DATA_DIR+"/"+cat+"-unused-libs.txt")

# collect per-app libs and lib counts
lib_counts = OrderedDict()
lib_3p_counts = OrderedDict()
p="w+"
for a in apps:
    write_list(apps[a]['imports'], RAW_DATA_DIR+"/"+cat+"-libs-perapp.txt", name=a, perm=p)
    lib_counts[a] = len(apps[a]['imports'])
    lib_3p_counts[a] = len(remove_stdlib_imports(apps[a]['imports']))
    if p == "w+":
        # want to set the perm to append after the first app
        p = "a+"

write_freq_map(lib_counts, filename="analysis/"+cat+"-lib-counts.txt", perm="w+")
write_freq_map(lib_3p_counts, filename="analysis/"+cat+"-3p-lib-counts.txt", perm="w+")

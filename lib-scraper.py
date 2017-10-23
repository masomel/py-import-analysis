# Given a set of apps under a certain category,
# this scrapes them for all imported libraries and
# sanitizes the result to obtain a list of all
# imported third-party libraries (a first-party library is a module
# that is part of the app that is imported)

import os
import sys
import subprocess
from queue import Queue
import time

from collections import OrderedDict

from util import *
from import_scraper import *

LIB_DIR = "../libs"
RAW_DATA_DIR = "raw"

# this goes through the entire lib hierarchy and looks for
# a C-implementation of the lib
def check_for_c_source(path, lib, is_ctypes=False):
    mods = lib.split(".")
    for m in mods:
        c, j = search_c_source(path, m, is_ctypes)
        if len(c) > 0:
            return True, c, j
    return False, c, j

def check_ctypes_wrapper(imps):
    for src, i in imps.items():
        lds = scan_source_ctypes(src)
        if len(lds) > 0:
            print("Found ctypes wrapper")
            return True, lds
    return False, []

longjmp_libs = []
def check_longjmps(jmps, lib):
    if len(jmps) > 0:
        if lib not in longjmp_libs:
            longjmp_libs.append(lib)

def get_shared_libs(c_list):
    shlibs = []
    for s in c_list:
        if s.endswith(".so"):
            shlibs.append(s)
    return shlibs

def count_shared_lib_freq(sh, lib, d):
    # first check to see if we already have an entry
    # for this lib in the given dict d
    if d.get(lib) is None:
        tmp = dict()
    else:
        tmp = d[lib]

    # now count the shared lib sh in the dict
    if tmp.get(sh) is None:
            tmp[sh] = 1
    else:
        tmp[sh] += 1

    d[lib] = tmp

def check_ext_proc_calls(imps):
    for src, i in imps.items():
        for l in i:
            if l == "os" or l == "subprocess" or l == "subprocess.call" or l == "subprocess.Popen" or "os." in l:
                c = scan_source_native(src)
                if len(c) > 0:
                    print("Found call to native proc")
                    return True
    return False

def compute_lib_path(lib, top_lib, top_lib_path):
    lib_path = LIB_DIR+"/"+lib
    if os.path.isdir(lib_path+"/"+lib):
        # this means that the lib has its own dir
        lib_path = lib_path+"/"+lib
    elif lib == "RPi.GPIO":
        # make an exception for RPi.GPIO since it's the
        # only lib that only has a subpackage
        lib_path = lib_path+"/RPi"
    # on rare occasions, the lib is just a python file
    elif os.path.isfile(lib_path+"/"+lib+".py"):
        lib_path = lib_path+"/"+lib+".py"
    # these three next cases cover downloaded dependencies
    elif os.path.isdir(top_lib_path+"/"+lib):
        lib_path = top_lib_path+"/"+lib
    elif os.path.isdir(top_lib_path+"/"+top_lib+"/"+lib):
        # this means that the lib has its own dir
        lib_path = top_lib_path+"/"+top_lib+"/"+lib
    elif os.path.isfile(top_lib_path+"/"+lib+".py"):
        lib_path = top_lib_path+"/"+lib+".py"
    elif os.path.isfile(top_lib_path+"/_"+lib+".py"):
        lib_path = top_lib_path+"/_"+lib+".py"
    return lib_path

dep_freq = dict()
dist_deps = []
c_shared_freq = dict()
ctypes_instances_freq = dict()
def get_libs_with_deps(names, top_lib, lib, visited, clibs, shlibs, extproc, lvl):
    if lvl > 0:
        print(lib+" is dependency for "+top_lib)
        if dep_freq.get(lib) == None:
            dep_freq[lib] = 1
            dist_deps.append(lib)
        else:
            dep_freq[lib] += 1

    lvl += 1
    no_pip = []

    print("---- "+lib)

    # this covers the case in which we download a lib we've seen in
    # a previous call of get_libs_with_deps
    if lib in clibs or lib in shlibs or lib in extproc:
        print("Found "+lib+" in c libs, shared libs, or ext proc calls")
        c = []
        s = []
        n = []
        if lib in clibs:
            c = [lib]
        if lib in shlibs:
            s = [lib]
        if lib in extproc:
            n = [lib]
        lvl -= 1
        return c, s, n, no_pip

    # the alternative name
    if names.get(lib) != None and names[lib] != "":
        downl = names[lib]
    else:
        downl = lib

    top_lib_path = LIB_DIR+"/"+top_lib
    lib_path = compute_lib_path(lib, top_lib, top_lib_path)

    try:
        if not os.path.isdir(lib_path) and not os.path.isfile(lib_path):
            time.sleep(5) # sleep 5s to make sure we're not clobbering pip
            print("Downloading "+downl)
            subprocess.check_output(["pip3", "install", "-qq", "--no-compile", "-t", LIB_DIR+"/"+lib, downl])

    except subprocess.CalledProcessError:
        # let's see if we can find any sources in the lib path
        has_c, srcs, jmps = check_for_c_source(top_lib_path, lib)
        if has_c:
            shlibs = get_shared_libs(srcs)
            for sh in shlibs:
                count_shared_lib_freq(sh, lib, c_shared_freq)
            print("Found dependency C-lib")
            lvl -= 1
            check_longjmps(jmps, lib)
            return [lib], [], [], []

        no_pip.append(lib)
        print("Did not install through pip: "+lib)
        lvl -= 1
        return [], [], [], no_pip

    # we might have dependency py files in our lib path
    search_path = lib_path
    if top_lib_path == LIB_DIR+"/"+lib and lib_path.endswith(".py"):
        search_path = top_lib_path

    print("Searching for imports in: "+search_path)

    imports_raw, unused_raw = extract_imports(cat, search_path, perm="a+")

    imps = OrderedDict()
    c_deps = OrderedDict()

    # this means pyflakes didn't find any .py files in the source
    if len(imports_raw) == 0 and len(unused_raw) == 0:
        print("No python sources found")
        lvl -= 1
        return [lib], [], [], []
    # this means pyflakes found a single empty __init__.py file
    elif len(imports_raw) == 1 and len(unused_raw) == 1 and imports_raw.get(search_path+"/__init__.py") != None and len(imports_raw.get(search_path+"/__init__.py")) == 0 and unused_raw.get(search_path+"/__init__.py") != None and len(unused_raw.get(search_path+"/__init__.py")) == 0:
        print("C implementation likely elsewhere (no imports)")
        lvl -= 1
        return [lib], [], [], []
    else:
        imps['unused'] = unused_raw
        imps['raw_imports'] = imports_raw

        # iterate over the raw_imports to replace any pkg-level
        # imports in any "unused" __init__.py files
        imps['raw_imports'] = replace_unused_init_imports(imps['raw_imports'], imps['unused'], search_path)

        # iterate over the raw_imports to add any pkg-level
        # imports in any "unused" __init__.py files
        # this is only done if the __init__.py file has no used imports
        imps['raw_imports'] = add_mod_init_imports(lib, imps['raw_imports'], imps['unused'])

        # at this point, if we've replaced the init imports
        # and the imports are still empty, we can be pretty
        # sure that we have a c implementation elsewhere
        if len(imps['raw_imports']) == 1 and imps['raw_imports'].get(search_path+"/__init__.py") != None and len(imps['raw_imports'].get(search_path+"/__init__.py")) == 0:
            print("C implementation likely elsewhere (with imports)")
            lvl -= 1
            return [lib], [], [], []
        else:
            hybrid_libs = []
            call_native = []

            # check to see if this lib is a ctypes wrapper
            is_ctypes, hybs = check_ctypes_wrapper(imps['raw_imports'])
            if is_ctypes:
                hybrid_libs.append(lib)
                ctypes_c, ct_cs, jmps = check_for_c_source(search_path, lib, True)
                hybs.extend(get_shared_libs(ct_cs))
                for h in hybs:
                    actual_h = extract_ctypes_shlib(h)
                    count_shared_lib_freq(actual_h, lib, ctypes_instances_freq)
                    
            if check_ext_proc_calls(imps['raw_imports']):
                call_native.append(lib)
                
            # let's do one more check for c sources at this point
            # in case we missed anything within the current lib pkg
            # remove any such libs from the imports
            clean = dict()
            clibsd = []
            for src, i in imps['raw_imports'].items():
                clean[src] = []
                for l in i:
                    has_c = False
                    c_srcs = []
                    jmps = []

                    has_c, c_srcs, jmps = check_for_c_source(search_path, l)

                    extra_src_dir = ""
                    for dp, dn, fn in os.walk(top_lib_path):
                        if "source" in dn:
                            extra_src_dir = os.path.join(dp, "source")
                        elif "src" in dn:
                            extra_src_dir = os.path.join(dp, "src")

                        if extra_src_dir != "":
                            has_c1, c_srcs1, jmps1 = check_for_c_source(extra_src_dir, l)
                            has_c = has_c or has_c1
                            c_srcs.extend(c_srcs1)
                            jmps.extend(jmps1)
                            
                    if has_c:
                        shlibs = get_shared_libs(c_srcs)
                        # we want to separate the .so files used in ctypes
                        # libs from the ones imported directly into python
                        for s in shlibs:
                            if (is_ctypes and s not in hybs) or not is_ctypes:
                                count_shared_lib_freq(s, lib, c_shared_freq)
                        print("Found a C-implementation")
                        clibsd.append(l)
                        check_longjmps(jmps, lib)
                    else:
                        clean[src].append(l)

            imps['raw_imports'] = clean

            # this is the main case where we need to replace libs etc
            # make sure to sort the sources to have a deterministic analysis
            imps['raw_imports'] = OrderedDict(sorted(imps['raw_imports'].items(), key=lambda t: t[0]))

            imps['imports'] = replace_fp_mod_group(imps, search_path, 'raw_imports', is_libs=True)

            # we only want to store the pkg names
            imps['imports'] = get_pkg_names(imps, 'imports')

            # iterate over all imports and prune away all std lib imports
            print("Removing all python std lib imports")
            imps['imports'] = remove_stdlib_imports(imps['imports'])

            # need to replace the modules in the c libs, too
            # and clean them up
            c_deps['raw'] = clibsd
            c_deps['clean'] = get_pkg_names(c_deps, 'raw')

            if len(imps['imports']) == 0:
                print("No 3p python imports")
                lvl -= 1
                return c_deps['clean'], hybrid_libs, call_native, []
            else:
                print("Found 3-p imports -- more analysis")
                for l in imps['imports']:
                    # by the second iteration, we may already
                    # have all the info we need about the characteristics
                    # of the lib
                    if len(c_deps['clean']) > 0 and len(hybrid_libs) > 0 and len(call_native) > 0:
                        break

                    # remove any 3p imports that are the lib itself
                    # remove any 3p imports of setuptools
                    # ignore Jython imports
                    # ignore special modules
                    if l != lib and l != "setuptools" and not (l.startswith("__") and l.endswith("__")) and not (l == "java" or l == "systemrestart"):
                        if l in visited:
                            print(l+" has already been analyzed")
                        else:
                            visited.append(l)
                            # let's start adding package exceptions
                            if l == "ntlm":
                                names[l] = "python-ntlm"
                            elif l == "OpenSSL":
                                names[l] = "pyOpenSSL"
                            elif l == "OpenGL":
                                names[l] = "PyOpenGL"
                            elif l == "dns":
                                names[l] = "dnspython"
                            elif l == "OpenGL_accelerate":
                                names[l] = "PyOpenGL_accelerate"
                            elif l == "stackless":
                                names[l] = "stackless-python"
                            elif l == "ndg":
                                names[l] = "ndg-httpsclient"
                            elif l.startswith("win32"):
                                names[l] = "pywin32"
                            c, hyb, n, np = get_libs_with_deps(names, lib, l, visited, clibs, shlibs, extproc, lvl)
                            c_deps['clean'].extend(c)
                            hybrid_libs.extend(hyb)
                            call_native.extend(n)
                            no_pip.extend(np)
            lvl -= 1
            return c_deps['clean'], hybrid_libs, call_native, no_pip

#### MAIN ###

cat = sys.argv[1]

# cleanup before we start
imps_f = "pyflakes-out/"+cat+"-imports.txt"
unused_f = "pyflakes-out/"+cat+"-unused.txt"
py3_report_f = "pyflakes-out/"+cat+"-py3-report.txt"
py2_report_f = "pyflakes-out/"+cat+"-py2-report.txt"
if os.path.isfile(imps_f):
    os.remove(imps_f)
if os.path.isfile(unused_f):
    os.remove(unused_f)
if os.path.isfile(py3_report_f):
    os.remove(py3_report_f)
if os.path.isfile(py2_report_f):
    os.remove(py2_report_f)

f = open(RAW_DATA_DIR+"/"+cat+"-libs.txt", "r")
libs = f.readlines()
f.close()

print("Number of libs in "+cat+": "+str(len(libs)))

# let's load all the libs with their alternative names
lib_names = OrderedDict()
for l in libs:
    pair = l.split(",")
    lib = pair[0].strip()
    lib_names[lib] = ""
    if len(pair) == 2:
        lib_names[lib] = pair[1].strip()

c_libs = []
call_native = []
hybrid_libs = []
no_pip = []
top_no_pip = []
py_libs = []
clibs = []
shlibs = []
execs = []
for l in libs:
    pair = l.split(",")
    lib = pair[0].strip()
    recurs_limit = []
    c_libs_top = []
    call_native_top = []
    hybrid_libs_top = []
    c, hyb, native, np = get_libs_with_deps(lib_names, lib, lib, recurs_limit, c_libs_top, hybrid_libs_top, call_native_top, 0)

    if len(c) == 0 and len(hyb) == 0 and len(native) == 0 and len(np) == 0:
        py_libs.append(lib)
    else:
        if len(c) > 0:
            clibs.append(lib)
        if len(hyb) > 0:
            shlibs.append(lib)
        if len(native) > 0:
            execs.append(lib)
        if len(np) > 0:
            if lib in np:
                top_no_pip.append(lib)
                # remove all occurrences of lib from np
                np = [y for y in np if y != lib]

            # if we already have all the info we need on this lib
            # ignore the libs we couldn't download
            if not (len(c) > 0 and len(hyb) > 0 and len(native) > 0):
                no_pip.extend(np)

        c_libs.extend(c)
        hybrid_libs.extend(hyb)
        call_native.extend(native)

no_pip = remove_dups(no_pip)
write_list_raw(no_pip, RAW_DATA_DIR+"/"+cat+"-no-pip.txt")
write_list_raw(top_no_pip, RAW_DATA_DIR+"/"+cat+"-failed.txt")
write_list_raw(py_libs, RAW_DATA_DIR+"/"+cat+"-py-libs.txt")

write_list_raw(execs, RAW_DATA_DIR+"/"+cat+"-ext-proc.txt")
write_list_raw(remove_dups(call_native), RAW_DATA_DIR+"/"+cat+"-ext-proc-deps.txt")
write_list_raw(clibs, RAW_DATA_DIR+"/"+cat+"-c-libs.txt")
write_list_raw(remove_dups(c_libs), RAW_DATA_DIR+"/"+cat+"-c-libs-deps.txt")
write_list_raw(shlibs, RAW_DATA_DIR+"/"+cat+"-ctypes.txt")
write_list_raw(remove_dups(hybrid_libs), RAW_DATA_DIR+"/"+cat+"-ctypes-deps.txt")
write_map(c_shared_freq, RAW_DATA_DIR+"/"+cat+"-shared-lib-freq.txt", perm="w+")
write_map(ctypes_instances_freq, RAW_DATA_DIR+"/"+cat+"-ctypes-shared-lib-freq.txt", perm="w+")
write_freq_map(dep_freq, "analysis/"+cat+"-dep-freq.txt", "w+")
write_list_raw(remove_dups(dist_deps), RAW_DATA_DIR+"/"+cat+"-unique-deps.txt")
write_list_raw(remove_dups(longjmp_libs), RAW_DATA_DIR+"/"+cat+"-longjmp-libs.txt")

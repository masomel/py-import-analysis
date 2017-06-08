import os
import sys

from collections import OrderedDict
import xmlrpc.client as xmlrpclib

from pyflakes import reporter as modReporter
from pyflakes.api import checkRecursive, iterSourceCode

from util import *

def extract_imports(cat, path, perm="w+"):
    f = open("pyflakes-out/"+cat+"-py3-report.txt", perm)
    reporter = modReporter.Reporter(f, f)
    # num = number of warnings, imps = used imports, un = unused imports
    num, imps, un = checkRecursive([path], reporter)
    f.close()

    #write_map(imps, "pyflakes-out/"+cat+"-imports-py3.txt", perm=perm, sort=True)
    #write_map(un, "pyflakes-out/"+cat+"-unused-py3.txt", perm=perm, sort=True)

    # the modules in this list are likely written in python2 so run pyflakes
    # on python2
    redir = ">"
    if perm == "a+":
        redir = ">>"
    os.system("python2 -m pyflakes "+path+" "+redir+" pyflakes-out/"+cat+"-py2-report.txt 2>&1")

    # now, let's parse the imports and unused
    imps_2 = read_map("pyflakes-out/imports-py2.txt")
    un_2 = read_map("pyflakes-out/unused-py2.txt")

    # the py2 run of flakes probably finds imports found by the py3 run
    # let's merge the two dicts
    # see: https://stackoverflow.com/questions/38987/how-to-merge-two-python-dictionaries-in-a-single-expression#26853961
    imports_raw = imps.copy()
    imports_raw.update(imps_2)
    unused_raw = un.copy()
    unused_raw.update(un_2)

    write_map(imports_raw, "pyflakes-out/"+cat+"-imports.txt", perm=perm, sort=True)
    write_map(unused_raw, "pyflakes-out/"+cat+"-unused.txt", perm=perm, sort=True)

    os.remove("pyflakes-out/imports-py2.txt")
    os.remove("pyflakes-out/unused-py2.txt")

    return imports_raw, unused_raw

def group_by(g, ungrouped):
    grouped = OrderedDict()
    for src, i in ungrouped.items():
        if g in src:
            # want raw_imports AND imports since raw_imports is used
            # in the unused parsing as well
            libs = remove_dups(i)
            grouped[src] = libs
    return grouped

def get_src_dir(path):
    dirs = path.split('/')
    script_idx = len(dirs)
    src_dir = "/".join(dirs[0:script_idx-1])
    return src_dir

# either return the app if the src dir is the app dir
# or return the dir above the source dir
def get_super_dir(app, path):
    if get_src_dir(path) == app:
        return app
    else:
        dirs = path.split('/')
        script_idx = len(dirs)
        super_dir = "/".join(dirs[0:script_idx-2])
        return super_dir

def get_top_pkg_name(name):
    if name.count('.') >= 1:
        mod = name.split('.')

        # this covers the ..module and .module cases
        # we might see in the lib scraper
        if mod[0] == "" and mod[1] == "":
            return mod[2]
        elif mod[0] == "":
            return mod[1]

        return mod[0]
    else:
        return ""

# this assumes path is a subdirectory of app
def get_top_pkg_from_path(app, path):
    app_comps = app.split("/")
    path_comps = path.split("/")
    return path_comps[len(app_comps)]

# we only want to store the top-level package
def get_pkg_names(app, target):
    print("Extracting package names for "+target)
    pkgs = []
    for lib in app[target]:
        tlp = get_top_pkg_name(lib)
        if lib == "RPi.GPIO" or lib == "encodings.idna" or lib == "xmlrpc.client":
            # let's make an exception for these 3 libs -- that's the pkg name
            tlp = lib
        elif "concurrent.futures" in lib:
            # need to make an exception for stdlib concurrent.futures
            tlp = "concurrent.futures"
        elif "mock" == lib:
            # mock is in the stdlib since 3.3 as part of unittest
            tlp = "unittest.mock"
        elif "pkg_resources" in lib:
            # pkg_resources is a subpackage of setuptools
            tlp = "setuptools"
        elif lib.startswith("Image"):
            # apparently, you can import all of PIL or just subpkgs directly
            # so just rename any PIL subpkg to PIL
            tlp = "PIL"
        elif lib.startswith("tk"):
            # same with Tkinter
            tlp = "Tkinter"
        elif tlp == "":
            tlp = lib
        pkgs.append(tlp)
    return remove_dups(pkgs)

def get_subdir_srcs(subdir):
    srcs = []
    # will want to look at the contents of the entire directory
    files = os.listdir(subdir)
    for f in files:
        if not f.startswith("."):
            srcs.append(subdir+"/"+f)
    return srcs

def replace_fp_mod(app, super_dir, src_dir, imp, srcs_dict, visited, is_libs=False):
    # apprently, we can have ".." in the middle of a module
    # so just ignore it and treat like single "."
    if ".." in imp and not (imp.startswith("..") or imp.startswith("...")):
        imp = imp.replace("..", ".")

    # let's get all the individual components of the import
    mods = imp.split(".")

    mod = ""
    supermod = ""
    incl_dep = ""
    single_imp = False
    src_dir_imp = False
    sibling_dir_imp = False
    higher_dir_imp = False
    incl_dep_imp = False
    pref = ""
    if len(mods) == 1:
        # we're importing a single name
        single_imp = True
        mod = mods[0]
    else:
        if src_dir.endswith("/"+mods[0]):
            src_dir_imp = True
            # we're importing a submodule from the src_dir
            # cut off the top-level module and keep all submodules
            mod = "/".join(mods[1:])
            supermod = "/".join(mods[1:len(mods)-1])
        elif super_dir.endswith("/"+mods[0]):
            sibling_dir_imp = True
            # we're importing a submodule from a sibling directory
            mod = "/".join(mods[1:])
            supermod = "/".join(mods[1:len(mods)-1])
        elif "/"+mods[0]+"/" in super_dir:
            higher_dir_imp = True
            # we're importing a submodule from a higher-up directory
            # this also means that neither src_dir nor super_dir are
            # the right prefix, so let's prune it
            mod = "/".join(mods)
            pref = super_dir[:super_dir.find("/"+mods[0])]
            supermod = "/".join(mods[:len(mods)-1])
        elif mods[0] == "" and mods[1] == "" and mods[2] == "" and mods[3] == "":
            higher_dir_imp = True
            # we're importing a ....submodule from a higher sibling_dir
            mod = "/".join(mods[4:])
            supermod = "/".join(mods[4:len(mods)-1])
            hierarch = super_dir.split("/")
            pref = "/".join(hierarch[:len(hierarch)-2])
        elif mods[0] == "" and mods[1] == "" and mods[2] == "":
            higher_dir_imp = True
            # we're importing a ...submodule from a higher sibling_dir
            mod = "/".join(mods[3:])
            supermod = "/".join(mods[3:len(mods)-1])
            hierarch = super_dir.split("/")
            pref = "/".join(hierarch[:len(hierarch)-1])
        elif mods[0] == "" and mods[1] == "":
            sibling_dir_imp = True
            # we're importing a ..submodule from the sibling_dir
            mod = "/".join(mods[2:])
            supermod = "/".join(mods[2:len(mods)-1])
            if is_libs and mods[2] == "packages":
                incl_dep_imp = True
                incl_dep = mods[3]
        elif mods[0] == "":
            src_dir_imp = True
            # we're importing a .module from the src_dir
            mod = "/".join(mods[1:])
            supermod = "/".join(mods[1:len(mods)-1])
            if is_libs and mods[1] == "packages":
                incl_dep_imp = True
                incl_dep = mods[2]
        else:
            # we're probably importing from some other dir in the app dir
            mod = "/".join(mods)
            supermod = "/".join(mods[:len(mods)-1])

    py_file = ""
    subdir = ""
    obj_mod = ""
    sibling_py_file = ""
    sibling_subdir = ""
    sibling_obj_mod = ""
    higher_py_file = ""
    higher_subdir = ""
    higher_obj_mod = ""
    init_file = ""
    subdir_init_file = ""
    sibling_init_file = ""
    if single_imp:
        # we're importing a single module
        # so we need to check if it's a py file in the src dir or
        # a subdir
        py_file = src_dir+"/"+mod+".py"
        subdir = src_dir+"/"+mod
        subdir_init_file = subdir+"/__init__.py"
        if is_libs:
            init_file = src_dir+"/__init__.py"
    elif src_dir_imp:
        debug("scr_dir_imp")
        # we're importing a module from the src dir
        # so we need to check if it's a py file in the src dir,
        # a subdir, or if the low-level pkg is actually an object
        # contained in a higher-level module
        py_file = src_dir+"/"+mod+".py"
        subdir = src_dir+"/"+mod
        if supermod != "":
            obj_mod = src_dir+"/"+supermod+".py"
            init_file = src_dir+"/"+supermod+"/__init__.py"
        # we might be importing an attribute defined in __init__.py
        # so treat the obj_mod as the src_dir
        else:
            obj_mod = src_dir+"/__init__.py"

        subdir_init_file = subdir+"/__init__.py"
        if incl_dep_imp:
            sibling_py_file = src_dir+"/"+incl_dep+".py"
    elif sibling_dir_imp:
        debug("sibling_dir_imp")
        # we're importing a module from a sibling dir
        # so we need to check if it's a py file in the sibling dir,
        # a subdir, or if the low=level pkg is actually an object
        # contained in a higher-level module
        sibling_py_file = super_dir+"/"+mod+".py"
        sibling_subdir = super_dir+"/"+mod
        if supermod != "":
            sibling_obj_mod = super_dir+"/"+supermod+".py"
            init_file = super_dir+"/"+supermod+"/__init__.py"
        else:
            # we might be importing an attribute defined in __init__.py
            # so treat the obj_mod as the src_dir
            sibling_obj_mod = super_dir+"/__init__.py"

        subdir_init_file = sibling_subdir+"/__init__.py"
        if incl_dep_imp:
            py_file = super_dir+"/"+incl_dep+".py"
    elif higher_dir_imp:
        debug("higher_dir_imp")
        # we're importing a module from a dir that's higher than the sibling
        # so we need to check if it's a py file in the higher dir,
        # a subdir, or if the low=level pkg is actually an object
        # contained in a higher-level module
        higher_py_file = pref+"/"+mod+".py"
        higher_subdir = pref+"/"+mod
        if supermod != "":
            higher_obj_mod = pref+"/"+supermod+".py"
            init_file = pref+"/"+supermod+"/__init__.py"
        # we might be importing an attribute defined in __init__.py
        # so treat the obj_mod as the src_dir
        else:
            higher_obj_mod = pref+"/__init__.py"

        subdir_init_file = higher_subdir+"/__init__.py"
    else:
        debug("undetermined import")
        # we're not sure where we're importing from
        # let's try all generic possibilities
        py_file = src_dir+"/"+mod+".py"
        subdir = src_dir+"/"+mod
        sibling_py_file = super_dir+"/"+mod+".py"
        sibling_subdir = super_dir+"/"+mod
        higher_py_file = app+"/"+mod+".py"
        higher_subdir = app+"/"+mod
        if supermod != "":
            obj_mod = src_dir+"/"+supermod+".py"
            sibling_obj_mod = super_dir+"/"+supermod+".py"
            higher_obj_mod = app+"/"+supermod+".py"
            init_file = app+"/"+supermod+"/__init__.py"
            subdir_init_file = src_dir+"/"+supermod+"/__init__.py"
            sibling_init_file = super_dir+"/"+supermod+"/__init__.py"
        else:
            # we might be importing an attribute defined in __init__.py
            # so treat the obj_mod as the src_dir
            obj_mod = src_dir+"/__init__.py"
            sibling_obj_mod = super_dir+"/__init__.py"
            higher_obj_mod = app+"/__init__.py"
            sibling_init_file = sibling_subdir+"/__init__.py"
            subdir_init_file = subdir+"/__init__.py"

    debug("Looking at "+py_file+", "+sibling_py_file+", "+higher_py_file+", "+obj_mod+", "+init_file+", "+sibling_obj_mod+", "+higher_obj_mod+", "+subdir_init_file+", "+sibling_init_file+", "+subdir+", "+sibling_subdir+" and "+higher_subdir)

    # let's check if none of the possible imports exist
    if srcs_dict.get(py_file) == None and srcs_dict.get(sibling_py_file) == None and srcs_dict.get(higher_py_file) == None and srcs_dict.get(init_file) == None and srcs_dict.get(obj_mod) == None and srcs_dict.get(sibling_obj_mod) == None and srcs_dict.get(higher_obj_mod) == None and srcs_dict.get(subdir_init_file) == None and srcs_dict.get(sibling_init_file) == None and not os.path.isdir(subdir) and not os.path.isdir(sibling_subdir) and not os.path.isdir(higher_subdir):
        debug("0")
        if is_libs and "packages/" in mod:
            # it's likely that this import is actually in the lib's dependency
            p = mod.split("/")
            dep_idx = 0
            for d in p:
                # traverse the source path until we find the dependency
                if d == "packages":
                    break
                dep_idx += 1
            # the actual lib being imported is under the dependency
            dep = ".".join(p[dep_idx+1:])
            return [dep]

        return [imp]

    else:
        #print(app+" $ "+pref+" $ "+imp)
        srcs = []
        case = ""
        if srcs_dict.get(py_file) != None:
            case = "1"
            srcs = [py_file]
        elif srcs_dict.get(sibling_py_file) != None:
            case = "2"
            srcs = [sibling_py_file]
        elif srcs_dict.get(higher_py_file) != None:
            case = "3"
            srcs = [higher_py_file]
        elif srcs_dict.get(init_file) != None:
            case = "4"
            srcs = [init_file]
        elif srcs_dict.get(obj_mod) != None:
            case = "5"
            srcs = [obj_mod]
        elif srcs_dict.get(sibling_obj_mod) != None:
            case = "6"
            srcs = [sibling_obj_mod]
        elif srcs_dict.get(higher_obj_mod) != None:
            case = "7"
            srcs = [higher_obj_mod]
        elif srcs_dict.get(subdir_init_file) != None:
            case = "8"
            srcs = [subdir_init_file]
        elif srcs_dict.get(sibling_init_file) != None:
            case = "9"
            srcs = [sibling_init_file]
        elif os.path.isdir(subdir):
            case = "10"
            srcs = iterSourceCode([subdir])
        elif os.path.isdir(sibling_subdir):
            case = "11"
            srcs = iterSourceCode([sibling_subdir])
        elif os.path.isdir(higher_subdir):
            case = "12"
            srcs = iterSourceCode([higher_subdir])

        debug(case)

        l = []
        for src in srcs:
            if src in visited:
                debug(src+" is imported recursively, so don't go deeper")
            else:
                visited.append(src)
                imps = srcs_dict[src]
                if src.endswith("__init__.py") and len(imps) == 0:
                    pass
                else:
                    for m in imps:
                        replacements = replace_fp_mod(app, get_super_dir(app, src), get_src_dir(src), m, srcs_dict, visited, is_libs)
                        l.extend(replacements)
        return l

def replace_fp_mod_group(grp_dict, g, target, is_libs=False):
    print("Replacing the first-party imports for group: "+target)
    libs = []
    for src, i in grp_dict[target].items():
        src_dir = get_src_dir(src)
        super_dir = get_super_dir(g, src)
        debug(" *** "+src)
        for l in i:
            try:
                # add entry for each src once we've tried to replace it
                recurs_limit = []
                # want this check bc we want to make sure we stay
                # within the app directory
                tmp = replace_fp_mod(g, super_dir, src_dir, l, grp_dict['raw_imports'], recurs_limit, is_libs)

                # this is just to avoid printing redundant messages
                if not(len(tmp) == 1 and tmp[0] == l):
                    debug("replacing "+l+" with "+str(tmp))
                libs.extend(tmp)
            except RecursionError:
                print("died trying to replace "+l+" in "+src)
                sys.exit(-1)
    return remove_dups(libs)

def call_native_proc(l):
    if "os.system" in l or "os.spawn" in l or "os.exec" in l or "os.popen" in l or "subprocess.call" in l or "subprocess.Popen" in l or "subprocess.run" in l or "subprocess.check_output" in l or "Popen(" in l or "call([" in l:
        return True
    return False

# collect all the native calls so proc collection is only about
# parsing those lines
def scan_source_native(src):
    f = open(src, "r")
    lines = f.readlines()
    f.close()
    # these are the calls to native code that we've observed
    nats = []
    nextLn = ""
    for l in lines:
        clean = l.strip()
        if not clean.startswith("#") and call_native_proc(clean):
            debug("Found call to native proc in code: "+clean)
            # let's make sure the actual command isn't actually
            # on the next line
            if ")" not in clean:
                nextLn = clean
            else:
                nats.append(clean)
        elif nextLn != "":
            nats.append(nextLn+clean)
            nextLn = ""
    return nats

# collect all the shared lib loads so proc collection is only about
# parsing those lines
def scan_source_ctypes(src):
    f = open(src, "r")
    lines = f.readlines()
    f.close()
    # these are the calls to native code that we've observed
    hybs = []
    for l in lines:
        clean = l.strip()
        if not clean.startswith("#") and ("CDLL(" in clean or "LoadLibrary(" in clean):
            debug("Found shared lib load in code: "+clean)
            hybs.append(clean)
    return hybs

def search_c_source(path, lib):
    c = []
    for dirpath, dirnames, filenames in os.walk(path):
        for f in filenames:
            f_hierarch = f.split("/")
            filename = f_hierarch[len(f_hierarch)-1] # the actual filename is the last element
            if (filename.startswith(lib+".") or filename.startswith("_"+lib+".")) and (filename.endswith(".c") or filename.endswith(".h") or filename.endswith(".cpp") or filename.endswith(".hpp") or filename.endswith(".so")):
                debug("Found C source: "+filename)
                c.append(filename)
    return c

def search_shared_libs(path, lib):
    shlibs = []
    for dirpath, dirnames, filenames in os.walk(path):
        for f in filenames:
            f_hierarch = f.split("/")
            filename = f_hierarch[len(f_hierarch)-1] # the actual filename is the last element
            if filename.startswith(lib+".") and filename.endswith(".so"):
                debug("Found shared lib: "+filename)
                shlibs.append(filename)
    return shlibs

def add_mod_init_imports(l, raw_imports, unused):
    mods = l.split(".")
    replaced_imps = OrderedDict()
    for src, i in raw_imports.items():
        new_i = []
        if len(i) == 0 and src.endswith("__init__.py"):
            init_unused = unused.get(src)
            if init_unused != None:
                for l_unused in init_unused:
                    if l_unused.startswith(mods[0]+"."):
                        new_i.append(l_unused)
                    # need to add a special case for wiringpi2 bc
                    # it's deprecated and uses wiringpi instead,
                    # which is implemented in c
                    # otherwise, wiringpi2 is marked as py-only, which is false
                    if l == "wiringpi2":
                        print("got here")
                        if l_unused.startswith("wiringpi"):
                            print(l_unused)
                            new_i.append(l_unused)
        else:
            new_i = i
        replaced_imps[src] = new_i
    return replaced_imps


def replace_unused_init_imports(raw_imports, unused, path):
    replaced_imps = OrderedDict()

    for src, i in raw_imports.items():
        new_i = []
        for l in i:
            mods = l.split(".")
            init_file = path+"/"+mods[0]+"/__init__.py"
            endidx = len(mods)-1
            # if we have an __init__.py file in the same pkg that has
            # unused imports we want to replace any of those in the
            # raw_imports entry for this src file
            init_unused = unused.get(init_file)
            replaced = False
            if init_unused != None and len(init_unused) > 0:
                debug("Source file: "+src+", lib: "+l)
                debug(path+"/"+mods[0]+" "+str(init_unused))
                for l_unused in init_unused:
                    mods_unused = l_unused.split(".")
                    endidx_unused = len(mods_unused)-1
                    if mods_unused[endidx_unused] == mods[endidx]:
                        new_i.append(mods[0]+"."+l_unused)
                        replaced = True
                        debug("Replacing "+l+" with "+mods[0]+"."+l_unused+" in init for "+src)
                        break
                if not replaced:
                    new_i.append(l)
            else:
                new_i.append(l)

        replaced_imps[src] = new_i
    return replaced_imps

def find_pip_name(lib):
    client = xmlrpclib.ServerProxy('https://pypi.python.org/pypi')
    search = client.search({'name': lib})
    found = False
    for l in search:
        pipname = l['name']
        if pipname == lib:
            print(pipname)
            found = True

    if not found:
        print(lib+": "+str(search))

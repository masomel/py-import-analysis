# Utility functions for the library stats scripts

import json
import os
from collections import OrderedDict
from stdlib_list import stdlib_list

STATS_FILE = "analysis/app-stats.txt"
DEBUG = False

def debug(msg):
    if DEBUG:
        print(str(msg))
        
def get_name(p):
    name = p[:p.find(".")]
    return name

def read_set(name):
    s_f = open(name, "r")
    s = s_f.readlines()
    s_f.close()
    s_clean = []
    for i in s:
        s_clean.append(i.rstrip())
    return s_clean

def is_native(lib):
    if ("- os" in lib) or ("- CLI" in lib) or (" - subprocess" in lib):
        return True
    return False

def is_3p_lib(l):
    libs2 = stdlib_list("2.7")
    libs3 = stdlib_list("3.4")
    libs35 = stdlib_list("3.5")
    if l not in libs2 and l not in libs3 and l not in libs35:
        return True
    return False

def remove_stdlib_imports(import_list):
    libs_3p = []
    for l in import_list:
        l1 = l.strip("'")
        if l.startswith("_") and not l.startswith("__"):
            l1 = l[1:]
        if is_3p_lib(l1) and l1 != "__builtin__" and l1 != "__future__" and l1 != "abcoll":
            libs_3p.append(l1)

    return libs_3p

def count_freq(to_count, m=None):
    if m == None:
        m = dict()
    for i in to_count:
        lib = i
        if m.get(lib) == None:
            m[lib] = 1
        else:
            m[lib] += 1
    return m

# expects a dict containing lists for different categories of the same data
def get_distinct(d):
    dis = []
    # iterate over the dict
    for cat in d:
        l = get_distinct_cat(cat, d)
        dis.extend(l)
    return remove_dups(dis)

def get_distinct_cat(cat, d):
    dis = []
    for lib in d[cat]:
        if lib not in dis:
            dis.append(lib)
    return dis

# we don't want to include libs['multi'] in this count since
# we'll be counting domain-unique libs that are used in
# multi-domain apps as non-unique
def get_common(libs, cat1='visual', cat2='audio', cat3='env'):
    # need to check all pairs to get the right count
    common_libs = dict()
    for lib in libs[cat1]:
        if lib in libs[cat2] or lib in libs[cat3]:
            if common_libs.get(lib) == None:
                common_libs[lib] = 1
            else:
                common_libs[lib] += 1

    for lib in libs[cat2]:
        if lib in libs[cat1] or lib in libs[cat3]:
            if common_libs.get(lib) == None:
                common_libs[lib] = 1
            else:
                common_libs[lib] += 1

    for lib in libs[cat3]:
        if lib in libs[cat1] or lib in libs[cat2]:
            if common_libs.get(lib) == None:
                common_libs[lib] = 1
            else:
                common_libs[lib] += 1

    return common_libs

# we don't want to include libs['multi'] in this count since
# we'll be counting domain-unique libs that are used in
# multi-domain apps as non-unique
def get_unique(libs, cat1='visual', cat2='audio', cat3='env'):
    # need to check all pairs to get the right count
    unique_libs = dict()
    vis = dict()
    for lib in libs[cat1]:
        if lib not in libs[cat2] and lib not in libs[cat3]:
            if vis.get(lib) == None:
                vis[lib] = 1
            else:
                vis[lib] += 1
    unique_libs[cat1] = vis

    aud = dict()
    for lib in libs[cat2]:
        if lib not in libs[cat1] and lib not in libs[cat3]:
            if aud.get(lib) == None:
                aud[lib] = 1
            else:
                aud[lib] += 1
    unique_libs[cat2] = aud

    env = dict()
    for lib in libs[cat3]:
        if lib not in libs[cat1] and lib not in libs[cat2]:
            if env.get(lib) == None:
                env[lib] = 1
            else:
                env[lib] += 1
    unique_libs[cat3] = env
    return unique_libs

# remove duplicate entries from a list
def remove_dups(l):
    return sorted(list(set(l)))

def read_map(filename):
    with open(filename, "r") as f:
        m = json.loads(f.read(), object_pairs_hook=OrderedDict)
    return m

def write_val(v, name, filename=STATS_FILE):
    f = open(filename, "a+")
    f.write("Number of "+name+": "+str(v)+"\n")
    f.close()

def write_str(v, s, filename=STATS_FILE):
    f = open(filename, "a+")
    f.write(s+": "+str(v)+"\n")
    f.close()

def write_list(l, filename, name=None, perm="a+"):
    f = open(filename, perm)
    if name != None:
        f.write(str(name)+":\n")
    f.write(json.dumps(l, indent=4)+"\n")
    f.close()

# TODO: merp, switch the default permission to "a+"
def write_list_raw(l, filename, perm="w+", sort=True):
    f = open(filename, perm)
    li = l
    if sort:
        li = sorted(l)
    for i in li:
        f.write(str(i)+"\n")
    f.close()

def write_map(m, filename, name=None, perm="a+", sort=False):
    f = open(filename, perm)
    if name != None:
        f.write(str(name)+":\n")
    d = m
    if sort:
        d = OrderedDict(sorted(m.items(), key=lambda t: t[0]))
    f.write(json.dumps(d, indent=4)+"\n")
    f.close()

def sort_freq_map(m):
    d = OrderedDict(sorted(m.items(), key=lambda kv: (-kv[1], kv[0])))
    return d

def map2list(m):
    l = []
    for k, v in m.items():
        l.append(k+": %.1f" % v)
    return l

def get_top_n_freq(n, m, total):
    d = sort_freq_map(m)
    count = 0
    top = OrderedDict()
    for l, ct in d.items():
        if count == n:
            break
        freq = (ct/total)*100
        top[l] = freq
        count += 1
    return top

# sort dict by values in descreasing order, then keys in regular order
# From http://stackoverflow.com/questions/9919342/sorting-a-dictionary-by-value-then-key
def write_freq_map(m, filename=STATS_FILE, perm="a+"):
    d = sort_freq_map(m)
    write_map(d, filename, perm=perm)

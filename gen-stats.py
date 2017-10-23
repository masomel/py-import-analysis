# Gather statistics about the collected IoT apps

import sys
from collections import OrderedDict
from statistics import mean, median

from util import *

def app_stats():
    # get all the apps
    apps = dict()
    apps['visual'] = read_set("raw/visual-apps.txt")
    apps['audio'] = read_set("raw/audio-apps.txt")
    apps['env'] = read_set("raw/env-apps.txt")
    apps['multi'] = read_set("raw/multi-apps.txt")

    # get total number of distinct apps
    distinct_apps = get_distinct(apps)

    num_apps = len(distinct_apps)

    #write_val(str(num_apps)+", "+str(len(apps['visual']))+", "+str(len(apps['audio']))+", "+str(len(apps['env']))+", "+str(len(apps['multi'])), "total apps, visual, audio, env, multi")

    write_val(num_apps, "analyzed IoT apps")

    # get all the libs
    libs = OrderedDict()
    libs['audio'] = read_set("raw/audio-libs.txt")
    libs['env'] = read_set("raw/env-libs.txt")
    libs['multi'] = read_set("raw/multi-libs.txt")
    libs['visual'] = read_set("raw/visual-libs.txt")

    # count the number of distinct libs among all lib sets
    distinct_libs = get_distinct(libs)
    num_all_libs = len(distinct_libs)

    # need to extract the 3p libs here to get a percentage
    # iterate over all imports and prune away all std lib imports
    distinct_3p = remove_stdlib_imports(distinct_libs)
    num_3p_libs = len(distinct_3p)

    libs3p = OrderedDict()
    for cat, l in libs.items():
        libs3p[cat] = remove_stdlib_imports(l)

    write_val(str(num_all_libs)+" ("+str(num_3p_libs)+")", "distinct libs (3p)")
    pct_3p_libs = "%.1f" % ((num_3p_libs/num_all_libs)*100)
    write_str(pct_3p_libs, "% 3p libs")
    write_list_raw(distinct_libs, "raw/all-libs.txt")
    write_list_raw(distinct_3p, "raw/all-3p-libs.txt")

    # get the number of apps with 3p libs
    perapp = OrderedDict()
    perapp['audio'] = read_map("raw/audio-libs-perapp.txt")
    perapp['env'] = read_map("raw/env-libs-perapp.txt")
    perapp['multi'] = read_map("raw/multi-libs-perapp.txt")
    perapp['visual'] = read_map("raw/visual-libs-perapp.txt")

    num_libs_w_3p = 0
    for cat, d in perapp.items():
        for a, l in d.items():
            for i in l:
                if is_3p_lib(i):
                    num_libs_w_3p += 1
                    break

    write_val(str(num_libs_w_3p), "apps that use one or more 3p libs")

    # let's get the min/median/max of imports and 3p imports
    counts = OrderedDict()
    counts['audio'] = read_map("analysis/audio-lib-counts.txt")
    counts['env'] = read_map("analysis/env-lib-counts.txt")
    counts['multi'] = read_map("analysis/multi-lib-counts.txt")
    counts['visual'] = read_map("analysis/visual-lib-counts.txt")

    all_counts = []
    for cat in counts:
        all_counts.extend(map(int, counts[cat].values()))

    counts_3p = OrderedDict()
    counts_3p['audio'] = read_map("analysis/audio-3p-lib-counts.txt")
    counts_3p['env'] = read_map("analysis/env-3p-lib-counts.txt")
    counts_3p['multi'] = read_map("analysis/multi-3p-lib-counts.txt")
    counts_3p['visual'] = read_map("analysis/visual-3p-lib-counts.txt")

    all_3p_counts = []
    for cat in counts_3p:
        all_3p_counts.extend(map(int, counts_3p[cat].values()))

    avg_lib_per_app = "%.1f" % mean(all_counts)
    write_str(str(min(all_counts))+"/"+str(median(all_counts))+"/"+str(max(all_counts))+"/"+str(avg_lib_per_app), "Number of imports per app (min/median/max/mean)")
    avg_3plib_per_app = "%.1f" % mean(all_3p_counts)
    write_str(str(min(all_3p_counts))+"/"+str(median(all_3p_counts))+"/"+str(max(all_3p_counts))+"/"+str(avg_3plib_per_app), "Number of 3p imports per app (min/median/max/mean)")

    # get all common libs
    common_libs = get_common(libs3p)

    # get all category-unique libs
    only_libs = get_unique(libs3p)

    # traverse the multi libs
    # add any lib that appears in any of the unique lists
    # to that list
    # otherwise, consider it a common lib
    for l in libs3p['multi']:
        if only_libs['visual'].get(l) != None:
            only_libs['visual'][l] += 1
        elif only_libs['audio'].get(l) != None:
            only_libs['audio'][l] += 1
        elif only_libs['env'].get(l) != None:
            only_libs['env'][l] += 1
        elif common_libs.get(l) != None:
            common_libs[l] += 1
        else:
            common_libs[l] = 1

    # now print the aggregate common and unique libs
    #write_val(len(common_libs), "common libs")
    write_freq_map(common_libs, filename="analysis/common-3p-lib-freq.txt", perm="w+")

    write_list_raw(common_libs.keys(), "raw/common-3p-libs.txt")

    #write_val(len(only_libs['audio']), "audio-only libs")
    write_freq_map(only_libs['audio'], filename="analysis/audio-3p-lib-freq.txt", perm="w+")
    #write_val(len(only_libs['env']), "env-only libs")
    write_freq_map(only_libs['env'], filename="analysis/env-3p-lib-freq.txt", perm="w+")
    #write_val(len(only_libs['visual']), "visual-only libs")
    write_freq_map(only_libs['visual'], filename="analysis/visual-3p-lib-freq.txt", perm="w+")

    # get overall top 5
    all_freq = OrderedDict()
    for typ in only_libs:
        for l, ct in only_libs[typ].items():
            all_freq[l] = ct

    for l, ct in common_libs.items():
        all_freq[l] = ct

    write_freq_map(all_freq, filename="analysis/all-lib-freq.txt", perm="w+")

    write_str("", "Top 5 libs by frequency (in % of apps)")
    write_list_raw(map2list(get_top_n_freq(5, all_freq, num_apps)), STATS_FILE, perm="a+", sort=False)

    # get the number of apps that call an external proc
    call_native = OrderedDict()
    call_native['audio'] = read_map("raw/audio-call-native.txt")
    call_native['env'] = read_map("raw/env-call-native.txt")
    call_native['multi'] = read_map("raw/multi-call-native.txt")
    call_native['visual'] = read_map("raw/visual-call-native.txt")

    num_ext_proc = 0
    for cat in call_native:
        num_ext_proc += len(call_native[cat])

    pct_ext_proc = "%.1f" % ((num_ext_proc/num_apps)*100)
    write_str(pct_ext_proc, "% of apps that exec an external proc")

    # get the number of apps that are hybrid
    hybrid = OrderedDict()
    hybrid['audio'] = read_map("raw/audio-hybrid-apps.txt")
    hybrid['env'] = read_map("raw/env-hybrid-apps.txt")
    hybrid['multi'] = read_map("raw/multi-hybrid-apps.txt")
    hybrid['visual'] = read_map("raw/visual-hybrid-apps.txt")

    num_hybrid = 0
    for cat in hybrid:
        num_hybrid += len(hybrid[cat])

    pct_hybrid = "%.1f" % ((num_hybrid/num_apps)*100)
    write_str(pct_hybrid, "% of apps that load libs thru ctypes")

    # get all the unused libs
    unused = OrderedDict()
    unused['audio'] = read_set("raw/audio-unused-libs.txt")
    unused['env'] = read_set("raw/env-unused-libs.txt")
    unused['multi'] = read_set("raw/multi-unused-libs.txt")
    unused['visual'] = read_set("raw/visual-unused-libs.txt")

    # count the frequency of each unused lib
    distinct_unused = OrderedDict()
    for cat in unused:
        distinct_unused = count_freq(unused[cat], distinct_unused)

    write_list_raw(distinct_unused.keys(), "raw/all-unused-libs.txt")

    # get the number of 3p libs in the unused
    unused_3p = OrderedDict()
    for l in distinct_unused:
        if is_3p_lib(l):
            unused_3p[l] = distinct_unused[l]

    write_val(str(len(distinct_unused))+" ("+str(len(unused_3p))+")", "unused libs (3p)")
    write_freq_map(distinct_unused, filename="analysis/unused-freq.txt", perm="w+")

    write_str("", "Top 5 unused 3p libs by frequency (in % of apps)")
    write_list_raw(map2list(get_top_n_freq(5, unused_3p, num_apps)), STATS_FILE, perm="a+", sort=False)

### Top 50 stats ###
def top50_lib_stats():
    top50_libs = read_set("raw/top50-libs.txt")
    
    top50 = OrderedDict()
    top50['c-libs'] = read_set("raw/top50-c-libs.txt")
    top50['hybrid-libs'] = read_set("raw/top50-ctypes.txt")
    top50['ext-proc'] = read_set("raw/top50-ext-proc.txt")
    top50_py_libs = read_set("raw/top50-py-libs.txt")

    common_top50 = get_common(top50, 'c-libs', 'hybrid-libs', 'ext-proc')
    only_top50 = get_unique(top50, 'c-libs', 'hybrid-libs', 'ext-proc')

    # get % of python libs
    pct_py_libs = "%.1f" % ((len(top50_py_libs)/50)*100)
    write_str(pct_py_libs, "% of pure python top-50 libs", filename="analysis/top50-lib-stats.txt")

    # get % of C libs
    pct_c_libs = "%.1f" % ((len(top50['c-libs'])/50)*100)
    pct_c_only = "%.1f" % ((len(only_top50['c-libs'])/50)*100)
    write_str(pct_c_libs+" ("+pct_c_only+")", "% of top-50 libs implemented in C/C++ (pure native)", filename="analysis/top50-lib-stats.txt")

    # get % of hybrid
    pct_hyb_libs = "%.1f" % ((len(top50['hybrid-libs'])/50)*100)
    pct_hyb_only = "%.1f" % ((len(only_top50['hybrid-libs'])/50)*100)
    write_str(pct_hyb_libs+" ("+pct_hyb_only+")", "% of top-50 libs that load .so thru ctypes (ctypes-only)", filename="analysis/top50-lib-stats.txt")
    
    # get % of libs that call an ext proc
    pct_ext_proc_libs = "%.1f" % ((len(top50['ext-proc'])/50)*100)
    pct_ext_only = "%.1f" % ((len(only_top50['ext-proc'])/50)*100)
    write_str(pct_ext_proc_libs+" ("+pct_ext_only+")", "% of top-50 libs that exec an external proc (exec-only)", filename="analysis/top50-lib-stats.txt")

    # get the % of libs that have at least two of these properties
    pct_common_libs = "%.1f" % ((len(common_top50)/50)*100)
    write_str(pct_common_libs, "% of top-50 libs that have at least two of these properties", filename="analysis/top50-lib-stats.txt")
    
    # get count of unique imported dependencies
    total_deps = read_set("raw/top50-unique-deps.txt")
    write_val(len(total_deps), "distinct dependencies", filename="analysis/top50-lib-stats.txt")

    # get top 5 dependencies
    dep_freq = read_map("analysis/top50-dep-freq.txt")
    write_str("", "Top 5 dependencies of top 50 libs", filename="analysis/top50-lib-stats.txt")
    write_list_raw(map2list_int(get_top_n(5, dep_freq)), "analysis/top50-lib-stats.txt", perm="a+", sort=False)

    # count how many of the top50 libs are also dependencies to top50
    dep_top50_num = 0
    for l in top50_libs:
        if l in total_deps:
            dep_top50_num += 1
    write_val(dep_top50_num, "top50 libs that are also dependencies", filename="analysis/top50-lib-stats.txt")

    so_freq_libs = read_map("raw/top50-shared-lib-freq.txt")

    # get count of unique native libs imported
    total_c = []
    for d, sos in so_freq_libs.items():
        for so in sos.keys():
            if so not in total_c:
                total_c.append(so)
    write_val(len(total_c), "distinct native dependencies", filename="analysis/top50-lib-stats.txt")

    # get top shared libs imported
    shlib_freq = count_overall_freq(so_freq_libs)
    write_val(len(shlib_freq.keys()), "distinct .so's imported directly as native dependencies", filename="analysis/top50-lib-stats.txt")
    write_freq_map(shlib_freq, filename="analysis/top50-distinct-shlib-freq.txt", perm="w+")
    write_str("", "Top 5 .so's imported directly (by # of occurrences)", filename="analysis/top50-lib-stats.txt")
    write_list_raw(map2list_int(get_top_n(5, shlib_freq)), "analysis/top50-lib-stats.txt", perm="a+", sort=False)

    # get count of unique ctypes libraries
    total_ctypes = read_set("raw/top50-ctypes-deps.txt")
    write_val(len(total_ctypes), "distinct dependencies that load .so thru ctypes", filename="analysis/top50-lib-stats.txt")

    # get top ctypes shared libs imported
    so_freq_libs = read_map("raw/top50-ctypes-shared-lib-freq.txt")
    shlib_freq = count_overall_freq(so_freq_libs)
    write_val(len(so_freq_libs.keys()), "distinct shared libs loaded via ctypes", filename="analysis/top50-lib-stats.txt")
    write_freq_map(shlib_freq, filename="analysis/top50-distinct-ctypes-shlib-freq.txt", perm="w+")
    write_str("", "Top 5 shared libs loaded by ctypes (by # of occurrences)", filename="analysis/top50-lib-stats.txt")
    write_list_raw(map2list_int(get_top_n(5, shlib_freq)), "analysis/top50-lib-stats.txt", perm="a+", sort=False)

    # get count of unique libs that exec an ext_proc
    total_execs = read_set("raw/top50-ext-proc-deps.txt")
    write_val(len(total_execs), "distinct dependencies that exec an external proc", filename="analysis/top50-lib-stats.txt")

## MAIN ##
if len(sys.argv) != 2:
    print("Usage: python3 gen_stats.py <app|top50-lib>")
    exit(-1)

stats_type = str(sys.argv[1])

STATS_FILE = "analysis/"+stats_type+"-stats.txt"
# remove an existing stats file since we'll want to override it
if os.path.isfile(STATS_FILE):
    os.remove(STATS_FILE)

if stats_type == "app":
    app_stats()
elif stats_type == "top50-lib":
    top50_lib_stats()

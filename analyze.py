'''
The tool used to analyze different python application import properties.
See the defined arguments for supported analyses of raw import data.

author: Marcela S. Melara
'''

import argparse

# Path hack to use our app analysis utils
import sys, os
sys.path.append(os.path.abspath('../app-analysis-utils'))
from record_data import write_list_raw, write_freq_map

from stats import basic_per_app_stats, distinct_libs, lib_frequency_count
from util import read_import_files

def default_analysis(perapp_imps):
    num_apps, stats_dict = basic_per_app_stats(perapp_imps)
    print("Number of analyzed apps: "+str(num_apps))
    print("Per-app import analysis:")
    stats_3p = stats_dict['3p']
    stats_all = stats_dict['all']
    print(" -- Number of third-party imports: mean = %d, min = %d, max = %d, median = %d" %
          (stats_3p['mean'], stats_3p['min'], stats_3p['max'], stats_3p['median']))
    print(" -- Number of all imports: mean = %d, min = %d, max = %d, median = %d" %
          (stats_all['mean'], stats_all['min'], stats_all['max'], stats_all['median']))

def distinct_import_analysis(perapp_imps):
    all_distinct, tp_distinct = distinct_libs(perapp_imps)
    count_all = len(all_distinct)
    count_3p = len(tp_distinct)
    print("Distinct per-app imports:")
    pct_3p_libs = (count_3p/count_all)*100
    print(" -- Number of distinct libraries (overall): %d" % count_all)
    print(" -- Number of distinct third-party libraries: %d (%.1f)" % (count_3p, pct_3p_libs))
    return all_distinct, tp_distinct

def import_frequency_analysis(perapp_imps):
    freq_dict, top50 = lib_frequency_count(perapp_imps)
    print("Top 5 third-party imports by % of apps:")
    print(" -- %s" % (', '.join(top50[:5])))
    return freq_dict, top50
    
parser = argparse.ArgumentParser(description='Analyze python application imports.')
parser.add_argument('dirs', metavar='d', type=str, nargs='+',
                    help='one or more paths to a directory containing raw per-application import files')
parser.add_argument('--distinct', action='store_true',
                    help='compute distinct number of imports')
parser.add_argument('-o', '--output', dest='save', type=str, nargs=1,
                    help='a path to a directory where intermediate data should be output')

args = parser.parse_args()

print(" -------- Python application import analysis --------")
perapp_imports = read_import_files(args.dirs)

default_analysis(perapp_imports)

if args.distinct:
    distinct_libs, distinct_3p = distinct_import_analysis(perapp_imports)
    freq_dict, top50 = import_frequency_analysis(perapp_imports)
    if args.save:
        write_list_raw(distinct_libs, args.save[0]+"/all-distinct-libs.txt")
        write_list_raw(distinct_3p, args.save[0]+"/3p-distinct-libs.txt")
        write_freq_map(freq_dict, args.save[0]+"/3p-lib-freq.txt", perm='w+')
        write_list_raw(top50, args.save[0]+"/top50-3p-libs.txt")

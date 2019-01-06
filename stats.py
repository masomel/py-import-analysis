'''
Library defining various functions for computing various statistics about
Python application imports.

author: Marcela S. Melara
'''

# Path hack to use our app analysis utils
import sys, os
sys.path.append(os.path.abspath('../pyapp-analysis-utils'))

from statistics import mean, median
from common import map2list
from data_processing import count_freq, get_top_n_freq
from util import remove_stdlib_imports

def __get_per_app_3p_imports(imports_dict):
    perapp_3ps = dict()
    for app, imps in imports_dict.items():
        perapp_3ps[app] = remove_stdlib_imports(imps)
    return perapp_3ps

# TODO: move this to app-analysis-utils.common
def per_key_count_list(data_dict):
    perkey_counts = []
    for k, vlist in data_dict.items():
        perkey_counts.append(len(vlist))
    return perkey_counts

def __basic_stats_dict(data_list):
    d = dict()
    d['min'] = min(data_list)
    d['max'] = max(data_list)
    d['mean'] = mean(data_list)
    d['median'] = median(data_list)
    return d

'''
Compute basic stats about the number of imports per app
in the given map:
mean, median, min and max number of imports.
'''
def basic_per_app_imports(perapp_imps):
    num_apps = len(perapp_imps)
    perapp_3ps = __get_per_app_3p_imports(perapp_imps)
    nums_3ps = per_key_count_list(perapp_3ps)
    app_3p_count = num_apps - nums_3ps.count(0)

    stats_dict = dict()
    stats_dict['all'] = __basic_stats_dict(per_key_count_list(perapp_imps))
    stats_dict['3p'] = __basic_stats_dict(nums_3ps)
    return num_apps, app_3p_count, stats_dict

'''
Find the distinct libraries imported into the apps
in the given map
'''
def distinct_libs(perapp_imps):
    distinct_libs = []
    for app, imps in perapp_imps.items():
        tmp = [ x for x in imps if x not in distinct_libs ]
        distinct_libs.extend(tmp)
    return distinct_libs, remove_stdlib_imports(distinct_libs)

'''
Count the number of apps each distinct third-party import
is included in, and return the top 5 imports
'''
def lib_frequency_count(perapp_imps):
    freq_dict = dict()
    perapp_3ps = __get_per_app_3p_imports(perapp_imps)
    for app, imps in perapp_3ps.items():
        count_freq(imps, freq_dict)
    return freq_dict, map2list(get_top_n_freq(50, freq_dict, len(perapp_3ps)))

'''
Compute basic stats about the depth of the depenency chain per app
in the given map:
mean, median, min and max number of dependency depth.
'''
def basic_per_app_dependency_depths(perapp_depths):
    stats_dict = dict()
    depths_list = [v for k, v in perapp_depths.items()]
    stats_dict['depths'] = __basic_stats_dict(depths_list)
    return stats_dict


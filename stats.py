'''
Library defining various functions for computing various statistics about
Python application imports.

author: Marcela S. Melara
'''

# Path hack to use our app analysis utils
import sys, os
sys.path.append(os.path.abspath('../app-analysis-utils'))

from statistics import mean, median
import record_data
import util

def __get_per_app_imports(paths_list):
    perapp = dict()
    for p in paths_list:
        imps_files = os.listdir(p)
        for f in imps_files:
            if f.endswith('-imports'):
                app_name = f[:-8]
                perapp[app_name] = util.get_package_fqns(record_data.read_set(p+'/'+f))
    print("Per-app dict of imports: "+str(perapp))
    return perapp

def __get_per_app_3p_imports(imports_dict):
    perapp_3ps = dict()
    for app, imps in imports_dict.items():
        perapp_3ps[app] = util.remove_stdlib_imports(imps)
    return perapp_3ps

# TODO: move this to app-analysis-utils.common
def per_key_count_list(data_dict):
    perkey_counts = []
    for k, vlist in data_dict.items():
        perkey_counts.append(len(vlist))
    print("Per-app list of import numbers: "+str(perkey_counts))
    return perkey_counts

def __basic_stats_dict(data_list):
    d = dict()
    d['min'] = min(data_list)
    d['max'] = max(data_list)
    d['mean'] = mean(data_list)
    d['median'] = median(data_list)
    return d

def basic_per_app_stats(paths_list):
    perapp_imps = __get_per_app_imports(paths_list)
    num_apps = len(perapp_imps)
    perapp_3ps = __get_per_app_3p_imports(perapp_imps)

    stats_dict = dict()
    stats_dict['all'] = __basic_stats_dict(per_key_count_list(perapp_imps))
    stats_dict['3p'] = __basic_stats_dict(per_key_count_list(perapp_3ps))
    return num_apps, stats_dict

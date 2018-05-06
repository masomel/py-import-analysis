'''
The tool used to analyze different python application import properties.
See the defined arguments for supported analyses of raw import data.

author: Marcela S. Melara
'''

import argparse
import stats

def default_analysis(paths_list):
    num_apps, stats_dict = stats.basic_per_app_stats(paths_list)
    print("Number of analyzed apps: "+str(num_apps))
    print("Per-app import analysis:")
    stats_3p = stats_dict['3p']
    stats_all = stats_dict['all']
    print(" -- Number of third-party imports: mean = %d, min = %d, max = %d, median = %d" %
          (stats_3p['mean'], stats_3p['min'], stats_3p['max'], stats_3p['median']))
    print(" -- Number of all imports: mean = %d, min = %d, max = %d, median = %d" %
          (stats_all['mean'], stats_all['min'], stats_all['max'], stats_all['median']))

parser = argparse.ArgumentParser(description='Analyze python application imports.')
parser.add_argument('dirs', metavar='d', type=str, nargs='+',
                    help='one or more paths to a directory containing raw per-application import files')

args = parser.parse_args()

print(" -------- Python application import analysis --------")
default_analysis(args.dirs)

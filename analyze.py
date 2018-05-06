'''
The tool used to analyze different python application import properties.
See the defined arguments for supported analyses of raw import data.

author: Marcela S. Melara
'''

import argparse

parser = argparse.ArgumentParser(description='Analyze python application imports.')
parser.add_argument('dirs', metavar='d', type=str, nargs='+',
                    help='one or more paths to a directory containing raw per-application import files')
parser.add_argument('-b', '--basic',
                    help='find the mean, min, max, median number of imports per application')

args = parser.parse_args()
print(args)

# collects the top n of the given frequency list
import sys

from util import read_map, get_top_n_freq, write_list_raw

if len(sys.argv) != 4:
    print("Usage: python3 get-top-n.py <n> <total> <freq-list-path>")
    exit(-1)

freq_list = read_map(sys.argv[3])
n = int(sys.argv[1])
total = int(sys.argv[2])

topn = get_top_n_freq(n, freq_list, total)
topn_list = []
for l in topn:
    topn_list.append(l)
write_list_raw(topn_list, "corpus/top"+str(n)+"-libs.txt", sort=False)

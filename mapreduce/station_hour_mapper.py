#!/usr/bin/env python3
# station_hour_mapper.py
# Input: cleansed journeys (CSV). Output: origin_stop|hour <TAB> 1
import sys

for line in sys.stdin:
    c = line.strip().split(",")
    if len(c) != 10:
        continue
    print("{0}|{1}\t1".format(c[5], c[3][11:13]))

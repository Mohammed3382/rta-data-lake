#!/usr/bin/env python3
# station_hour_reducer.py
# Adds up the 1s for every origin_stop|hour key.
import sys

current, total = None, 0
for line in sys.stdin:
    key, val = line.rstrip("\n").split("\t")
    if key != current:
        if current is not None:
            stop, hour = current.split("|")
            print("{0},{1},{2}".format(stop, hour, total))
        current, total = key, 0
    total += int(val)

if current is not None:
    stop, hour = current.split("|")
    print("{0},{1},{2}".format(stop, hour, total))

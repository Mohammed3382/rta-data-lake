#!/usr/bin/env python3
# its_speed_reducer.py
# Average speed per road, and a congestion flag.
import sys

def out(road, total, n):
    avg = total / n
    status = "CONGESTED" if avg < 40 else ("SLOW" if avg < 70 else "FREE FLOW")
    print("{0}\t{1:.1f}\t{2}".format(road, avg, status))

current, total, n = None, 0.0, 0
for line in sys.stdin:
    road, speed = line.rstrip("\n").split("\t")
    if road != current:
        if current is not None:
            out(current, total, n)
        current, total, n = road, 0.0, 0
    total += float(speed)
    n += 1

if current is not None:
    out(current, total, n)

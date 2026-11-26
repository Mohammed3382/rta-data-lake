#!/usr/bin/env python3
# its_speed_mapper.py
# Input: ITS sensor CSV. Output: road <TAB> speed
import sys

for line in sys.stdin:
    c = line.strip().split(",")
    if len(c) != 7 or c[0] == "sensor_id":
        continue
    print("{0}\t{1}".format(c[1], c[5]))

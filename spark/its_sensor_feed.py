#!/usr/bin/env python3
# its_sensor_feed.py
# Simulates the road sensor (loop detector) feed. Every few seconds it writes a
# small CSV of readings and puts it in the HDFS landing folder, the same way a
# real collector would drop files for the stream job.
#
# usage: python3 its_sensor_feed.py [number_of_files] [seconds_between_files]
# defaults: 12 files, one every 8 seconds (what we used in the report)

import os
import random
import subprocess
import sys
import time
from datetime import datetime

SENSORS = [
    ("E11-TC-01", "Sheikh Zayed Rd (Trade Centre)", "S", 55),
    ("E11-BB-02", "Sheikh Zayed Rd (Business Bay)", "S", 45),
    ("E11-AB-03", "Sheikh Zayed Rd (Al Barsha)", "S", 80),
    ("E11-MR-04", "Sheikh Zayed Rd (Marina)", "N", 85),
    ("E44-AK-01", "Al Khail Rd (Al Quoz)", "S", 75),
    ("E311-MZ-01", "Sheikh Mohammed bin Zayed Rd", "N", 95),
    ("E11-IT-01", "Al Ittihad Rd (to Sharjah)", "N", 30),
    ("D89-MB-01", "Al Maktoum Bridge", "E", 35),
    ("D85-GB-01", "Al Garhoud Bridge", "W", 50),
    ("D71-BB-01", "Business Bay Crossing", "E", 60),
]

n_files = int(sys.argv[1]) if len(sys.argv) > 1 else 12
gap = float(sys.argv[2]) if len(sys.argv) > 2 else 8
hadoop = os.path.join(os.environ["HADOOP_HOME"], "bin", "hadoop")
os.makedirs("/tmp/its", exist_ok=True)
subprocess.call([hadoop, "fs", "-mkdir", "-p", "/datalake/landing/_staging", "/datalake/landing/its_sensors"])

for i in range(n_files):
    now = datetime.now()
    name = "/tmp/its/its_{0}.csv".format(now.strftime("%Y%m%d_%H%M%S"))
    with open(name, "w") as f:
        f.write("sensor_id,road,direction,reading_ts,vehicles,avg_speed_kmh,occupancy_pct\n")
        for sid, road, d, base in SENSORS:
            for _ in range(6):   # 6 readings per sensor per file
                speed = max(5, random.gauss(base, 8))
                veh = int(max(0, random.gauss(40 - speed / 4, 6)))
                occ = round(min(95, max(2, 100 - speed * 0.8 + random.gauss(0, 4))), 1)
                f.write("{0},{1},{2},{3},{4},{5:.1f},{6}\n".format(
                    sid, road, d, now.strftime("%Y-%m-%d %H:%M:%S"), veh, speed, occ))
    # put into a staging folder first, then move. The move is atomic in HDFS,
    # so the stream job never reads a half-copied file.
    subprocess.call([hadoop, "fs", "-put", name, "/datalake/landing/_staging/"])
    subprocess.call([hadoop, "fs", "-mv", "/datalake/landing/_staging/" + os.path.basename(name),
                     "/datalake/landing/its_sensors/"])
    print("sent {0}".format(os.path.basename(name)))
    sys.stdout.flush()
    time.sleep(gap)

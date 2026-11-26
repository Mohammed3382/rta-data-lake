#!/bin/bash
# Sends simulated road sensor files into the landing zone (run this in a second
# terminal while 04_spark_stream.sh is running). 12 files, one every 8 seconds.

cd "$(dirname "$0")/../spark"
python3 its_sensor_feed.py 12 8

$HADOOP_HOME/bin/hadoop fs -ls /datalake/landing/its_sensors | head -6
$HADOOP_HOME/bin/hadoop fs -ls /datalake/curated/its_speed_1min | head -6
$HADOOP_HOME/bin/hadoop fs -count /datalake/landing/its_sensors /datalake/curated/its_speed_1min

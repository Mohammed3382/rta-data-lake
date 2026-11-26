#!/bin/bash
# Creates the five zones in HDFS and loads the raw data.
# Expects the GTFS feed in ~/rta_data/gtfs and the Nol files in ~/rta_data/nol
# (see the README for how to get both).

DATA=~/rta_data
HDFS="$HADOOP_HOME/bin/hadoop fs"

$HDFS -mkdir -p /datalake/raw/nol_taps /datalake/raw/gtfs /datalake/landing/its_sensors
$HDFS -mkdir -p /datalake/cleansed /datalake/curated /datalake/sandbox
$HDFS -ls /datalake

# one dt= folder per day
for d in 05 06 07 08 09 10 11; do
    $HDFS -mkdir -p /datalake/raw/nol_taps/dt=2026-10-$d
    $HDFS -put -f $DATA/nol/nol_taps_202610$d.csv /datalake/raw/nol_taps/dt=2026-10-$d/
done

# one folder per GTFS table
for t in stops routes trips stop_times; do
    $HDFS -mkdir -p /datalake/raw/gtfs/$t
    $HDFS -put -f $DATA/gtfs/$t.txt /datalake/raw/gtfs/$t/
done

$HDFS -du -h /datalake/raw
$HADOOP_HOME/bin/hdfs fsck /datalake/raw -files -blocks | tail -21

#!/bin/bash
# Cleans the Nol taps and builds journeys (raw zone -> cleansed zone).
# First a quick local test on 3,000 lines, then the real job on YARN.

cd "$(dirname "$0")/../mapreduce"
STREAMING=$HADOOP_HOME/share/hadoop/tools/lib/hadoop-streaming-2.7.3.jar

echo "--- local test on 3,000 lines"
$HADOOP_HOME/bin/hadoop fs -cat /datalake/raw/nol_taps/dt=2026-10-05/nol_taps_20261005.csv 2>/dev/null \
    | head -3000 | python3 nol_clean_mapper.py \
    | LC_ALL=C sort -t$'\t' -k1,1 | python3 nol_journey_reducer.py | head -8

echo "--- full job"
$HADOOP_HOME/bin/hadoop fs -rm -r -f /datalake/cleansed/nol_journeys
time $HADOOP_HOME/bin/hadoop jar $STREAMING \
    -D mapreduce.job.name="Nol cleansing" \
    -D mapreduce.job.reduces=4 \
    -files nol_clean_mapper.py,nol_journey_reducer.py \
    -mapper "/usr/bin/python3 nol_clean_mapper.py" \
    -reducer "/usr/bin/python3 nol_journey_reducer.py" \
    -input /datalake/raw/nol_taps/dt=* \
    -output /datalake/cleansed/nol_journeys

$HADOOP_HOME/bin/hadoop fs -ls /datalake/cleansed/nol_journeys
$HADOOP_HOME/bin/hadoop fs -cat /datalake/cleansed/nol_journeys/part-00000 | head -5

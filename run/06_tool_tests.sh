#!/bin/bash
# The tool comparison from section 5.9 of the report.
# 1-3: the same question (journeys per origin station per hour) in MapReduce, Hive and Spark
# 4:   MapReduce on a single sensor file, to compare with the ~2 s Spark batches

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
STREAMING=$HADOOP_HOME/share/hadoop/tools/lib/hadoop-streaming-2.7.3.jar
HDFS="$HADOOP_HOME/bin/hadoop fs"
$HDFS -rm -r -f /datalake/sandbox/station_hourly_mr /datalake/sandbox/station_hourly_hive \
    /datalake/sandbox/station_hourly_spark /datalake/sandbox/its_speed_mr

echo "--- 1. MapReduce"
cd "$ROOT/mapreduce"
time $HADOOP_HOME/bin/hadoop jar $STREAMING \
    -D mapreduce.job.name="Station hourly (MR)" -D mapreduce.job.reduces=4 \
    -files station_hour_mapper.py,station_hour_reducer.py \
    -mapper "/usr/bin/python3 station_hour_mapper.py" \
    -reducer "/usr/bin/python3 station_hour_reducer.py" \
    -input /datalake/cleansed/nol_journeys -output /datalake/sandbox/station_hourly_mr

echo "--- 2. Hive"
time $HIVE_HOME/bin/beeline -u jdbc:hive2://localhost:10000 -n $USER --silent=true -e \
"insert overwrite directory '/datalake/sandbox/station_hourly_hive' row format delimited fields terminated by ',' \
select origin_stop, hour(entry_ts), count(*) from rta_lake.cln_nol_journeys group by origin_stop, hour(entry_ts);"

echo "--- 3. Spark"
cd "$ROOT/spark"
time $SPARK_HOME/bin/spark-submit --master yarn --num-executors 3 --executor-cores 2 station_hourly.py

echo "--- 4. MapReduce on one sensor file"
FILE=$($HDFS -ls /datalake/landing/its_sensors | awk '{print $8}' | grep '\.csv$' | head -1)
cd "$ROOT/mapreduce"
time $HADOOP_HOME/bin/hadoop jar $STREAMING \
    -D mapreduce.job.name="ITS speed one file (MR)" \
    -files its_speed_mapper.py,its_speed_reducer.py \
    -mapper "/usr/bin/python3 its_speed_mapper.py" \
    -reducer "/usr/bin/python3 its_speed_reducer.py" \
    -input "$FILE" -output /datalake/sandbox/its_speed_mr
$HDFS -cat /datalake/sandbox/its_speed_mr/part-*

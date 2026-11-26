#!/bin/bash
# Starts the Spark Structured Streaming job (landing zone -> curated zone).
# Leave it running, open a second terminal and run 05_sensor_feed.sh.
# Stop it with Ctrl+C when the feed has finished.

cd "$(dirname "$0")/../spark"
$SPARK_HOME/bin/spark-submit --master yarn traffic_stream.py

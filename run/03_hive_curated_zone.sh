#!/bin/bash
# Runs the three Hive scripts through Beeline (HiveServer2 must be running).
# 01: external tables over the raw zone
# 02: cleansed journeys table and the star schema in the curated zone (about 3 min)
# 03: sample OLAP queries (the ones shown in Zeppelin)

cd "$(dirname "$0")/../hive"
BEELINE="$HIVE_HOME/bin/beeline -u jdbc:hive2://localhost:10000 -n $USER"

$BEELINE -f 01_raw_zone.hql
$BEELINE -f 02_curated_zone.hql
$BEELINE -f 03_olap_queries.hql

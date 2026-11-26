#!/bin/bash
# Starts everything the project needs, in the same order as the labs.
# HiveServer2 takes about 40 seconds before Beeline can connect.

$ZEPPELIN_HOME/bin/zeppelin-daemon.sh start
$HADOOP_HOME/sbin/hadoop-daemon.sh start namenode
$HADOOP_HOME/sbin/hadoop-daemon.sh start datanode
$HADOOP_HOME/sbin/yarn-daemon.sh start resourcemanager
$HADOOP_HOME/sbin/yarn-daemon.sh start nodemanager
$HADOOP_HOME/sbin/mr-jobhistory-daemon.sh start historyserver

# Hive metastore and HiveServer2 stay in the foreground, so we run them in the
# background here and keep their logs in the home folder.
nohup $HIVE_HOME/bin/hive --service metastore > ~/metastore.log 2>&1 &
sleep 20
nohup $HIVE_HOME/bin/hiveserver2 > ~/hiveserver2.log 2>&1 &

sleep 5
jps
echo "Wait about 40 seconds for HiveServer2, then continue with 01_load_raw_zone.sh"

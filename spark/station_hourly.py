# station_hourly.py
# Batch job: number of journeys per origin station per hour for the whole week.
# Same question as the MapReduce and Hive versions, used to compare run times.
#
# run with:
#   $SPARK_HOME/bin/spark-submit --master yarn station_hourly.py

import time
from pyspark.sql import SparkSession
from pyspark.sql.functions import hour, count, col

t0 = time.time()
spark = SparkSession.builder.appName("RTA station hourly (Spark)").getOrCreate()
spark.sparkContext.setLogLevel("WARN")

cols = ["card_id", "card_type", "mode", "entry_ts", "exit_ts", "origin_stop",
        "dest_stop", "duration_min", "fare_aed", "travel_date"]
j = (spark.read.csv("hdfs://localhost:8020/datalake/cleansed/nol_journeys")
     .toDF(*cols))

result = (j.groupBy("origin_stop", hour(col("entry_ts")).alias("hour"))
          .agg(count("*").alias("journeys"))
          .orderBy(col("journeys").desc()))

result.write.mode("overwrite").csv("hdfs://localhost:8020/datalake/sandbox/station_hourly_spark")
result.show(10)
print("Spark job finished in {0:.1f} seconds".format(time.time() - t0))

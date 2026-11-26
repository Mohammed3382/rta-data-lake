# traffic_stream.py
# Spark Structured Streaming job for ITS road sensor readings.
# Watches the landing folder in HDFS, works out the average speed per road
# for every 1 minute window, and flags congestion (average speed under 40 km/h).
#
# run with:
#   $SPARK_HOME/bin/spark-submit --master yarn traffic_stream.py

import time

from pyspark.sql import SparkSession
from pyspark.sql.functions import window, avg, sum as _sum, col, when, round as _round
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, DoubleType, TimestampType

spark = (SparkSession.builder.appName("RTA ITS traffic stream")
         .config("spark.sql.shuffle.partitions", "4")   # default is 200, far too many for small batches
         .getOrCreate())
spark.sparkContext.setLogLevel("WARN")

schema = StructType([
    StructField("sensor_id", StringType()),
    StructField("road", StringType()),
    StructField("direction", StringType()),
    StructField("reading_ts", TimestampType()),
    StructField("vehicles", IntegerType()),
    StructField("avg_speed_kmh", DoubleType()),
    StructField("occupancy_pct", DoubleType()),
])

readings = (spark.readStream
            .schema(schema)
            .option("header", "true")
            .option("maxFilesPerTrigger", 1)
            .csv("hdfs://localhost:8020/datalake/landing/its_sensors"))

per_minute = (readings
              .withWatermark("reading_ts", "2 minutes")
              .groupBy(window(col("reading_ts"), "1 minute"), col("road"))
              .agg(_round(avg("avg_speed_kmh"), 1).alias("avg_speed"),
                   _sum("vehicles").alias("vehicles"))
              .withColumn("status", when(col("avg_speed") < 40, "CONGESTED")
                                    .when(col("avg_speed") < 70, "SLOW")
                                    .otherwise("FREE FLOW")))

# console sink so the operators (and us) can watch it live
console = (per_minute.writeStream
           .outputMode("update")
           .format("console")
           .option("truncate", "false")
           .option("numRows", 12)
           .trigger(processingTime="10 seconds")
           .start())

# curated zone sink (Parquet) for later analysis in Hive / Zeppelin
to_lake = (per_minute.writeStream
           .outputMode("append")
           .format("parquet")
           .option("path", "hdfs://localhost:8020/datalake/curated/its_speed_1min")
           .option("checkpointLocation", "hdfs://localhost:8020/datalake/checkpoints/its_speed_1min")
           .trigger(processingTime="10 seconds")
           .start())

# print how long each micro-batch took, so we can compare with MapReduce
last = -1
while console.isActive:
    p = console.lastProgress
    if p and p["batchId"] != last and p["numInputRows"] > 0:
        last = p["batchId"]
        print("batch {0}: {1} rows processed in {2} ms".format(
            p["batchId"], p["numInputRows"], p["durationMs"].get("triggerExecution")))
    time.sleep(2)

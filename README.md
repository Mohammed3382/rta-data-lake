# RTA Data Lake

A small Hadoop data lake for Dubai's Roads and Transport Authority (RTA), built for ISIT312 Big Data Management (Autumn 2026). It runs on the course BigDataVM in Oracle VirtualBox: HDFS, MapReduce, Hive, Spark and Zeppelin on a single node.

It has two pipelines:

```
A. Daily Nol batch
   raw zone (one dt= folder per day)
     -> MapReduce (Python, Hadoop Streaming): clean taps, build journeys
     -> cleansed zone
     -> Hive: star schema stored as ORC
     -> curated zone -> Zeppelin / Beeline queries

B. Road sensor stream
   landing zone (a new file every 8 s)
     -> Spark Structured Streaming: 1 minute average speed per road
     -> console (alerts) + Parquet in the curated zone
```

The data lake lives in HDFS under `/datalake`, split into five zones: `landing`, `raw`, `cleansed`, `curated` and `sandbox`.

## Folders

| Folder | What is in it |
|---|---|
| `data_generator/` | `generate_nol_taps.py` makes one week of synthetic Nol taps from the real GTFS stations |
| `mapreduce/` | Nol cleansing mapper and reducer, plus the two small jobs used in the tool tests |
| `hive/` | `01` raw zone external tables, `02` star schema in the curated zone, `03` OLAP queries |
| `spark/` | Streaming job, sensor feed simulator, and the batch job used in the tool tests |
| `run/` | Shell scripts that run every step in order, with the same commands we used |

## Requirements

The course BigDataVM (or the same versions on Ubuntu 16.04):

- Hadoop 2.7.3 (pseudo-distributed), Hive 2.3.9 with HiveServer2, Spark 2.4.8 on YARN, Zeppelin 0.8.2
- Python 3.5 at `/usr/bin/python3`. Every script works on 3.5, with no extra packages.
- `HADOOP_HOME`, `HIVE_HOME`, `SPARK_HOME` and `ZEPPELIN_HOME` set, as they are on the course VM
- About 2 GB of free disk space for the data

## Getting the data

1. **GTFS timetable (real).** The Dubai RTA feed from the Mobility Database (feed `mdb-3359`). The feed is updated from time to time, so a newer version may give slightly different numbers.

```bash
mkdir -p ~/rta_data/gtfs && cd ~/rta_data/gtfs
wget https://files.mobilitydatabase.org/mdb-3359/latest.zip
python3 -m zipfile -e latest.zip .
cd -
```

2. **Nol taps (synthetic).** The RTA does not publish raw tap data, so we generate it:

```bash
python3 data_generator/generate_nol_taps.py ~/rta_data/gtfs ~/rta_data/nol
```

This writes seven files, `nol_taps_20261005.csv` to `nol_taps_20261011.csv`, about 110 to 145 MB each. The random seed is fixed, so the same feed always gives the same data.

## Running it

Copy or clone this folder onto the VM, then run the steps in order:

```bash
chmod +x run/*.sh
run/00_start_services.sh        # HDFS, YARN, JobHistory, Zeppelin, Hive metastore, HiveServer2
run/01_load_raw_zone.sh         # create the zones, load Nol and GTFS into the raw zone
run/02_mapreduce_cleansing.sh   # local test on 3,000 lines, then the full cleansing job
run/03_hive_curated_zone.sh     # external tables, star schema, sample OLAP queries
run/04_spark_stream.sh          # terminal 1: start the stream job and leave it running
run/05_sensor_feed.sh           # terminal 2: send 12 sensor files, one every 8 s
run/06_tool_tests.sh            # the same query in MapReduce, Hive and Spark
```

Web UIs: NameNode `localhost:50070`, YARN `localhost:8088`, Zeppelin `localhost:8080`.

For Zeppelin, create a note and paste the queries from `hive/03_olap_queries.hql` into `%hive` paragraphs.

## Results on our VM (6 vCPUs, 8 GB RAM)

| Step | Result |
|---|---|
| Raw zone | 918.1 MB of Nol taps and 135.3 MB of GTFS, 17 blocks, healthy |
| Nol cleansing (MapReduce, 9 maps, 4 reducers) | 11,630,326 lines in, 5,668,700 journeys out, 2 min 35 s |
| Cleansing counters | 23,178 duplicates removed, 23,139 old timestamps fixed, 11,742 missing stop and 431 test card taps rejected |
| Station by hour, full week | MapReduce 30.1 s, Hive 37.5 s, Spark 80.4 s |
| One sensor file (60 rows) | MapReduce 21.9 s, Spark streaming about 2 s per batch |

Times will differ on other machines, but the counts should match exactly.

## Notes

- Replication is 1 because the VM has only one DataNode.
- Hadoop Streaming adds a tab at the end of every output line. That is why `fact_journey` takes `travel_date` from `entry_ts`.
- The stream job sets `spark.sql.shuffle.partitions` to 4. The default of 200 made the first batch take 35 s on the VM.
- Kafka, Kerberos and Ranger are part of the design only. They are not on the course VM.

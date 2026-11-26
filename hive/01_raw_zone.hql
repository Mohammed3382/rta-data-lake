-- 01_raw_zone.hql
-- External tables over the raw zone. Data stays where it landed in HDFS,
-- Hive only keeps the table definition in the metastore.

create database if not exists rta_lake
comment 'RTA data lake: Nol taps, GTFS timetable, ITS sensors'
location '/datalake/hive/rta_lake.db';

use rta_lake;

-- Nol tap records, one folder per day (dt=YYYY-MM-DD)
create external table if not exists raw_nol_taps(
  txn_id     string,
  card_id    string,
  card_type  string,
  tap_ts     string,
  stop_id    string,
  gate_id    string,
  tap_type   string,
  fare_aed   string,
  mode       string)
partitioned by (dt string)
row format delimited fields terminated by ','
stored as textfile
location '/datalake/raw/nol_taps'
tblproperties ('skip.header.line.count'='1');

msck repair table raw_nol_taps;

-- RTA GTFS timetable feed (values are quoted, so OpenCSVSerde is used)
create external table if not exists raw_gtfs_stops(
  stop_id string, stop_name string, stop_lat string, stop_lon string,
  zone_id string, location_type string, stop_code string, stop_desc string, stop_url string)
row format serde 'org.apache.hadoop.hive.serde2.OpenCSVSerde'
stored as textfile
location '/datalake/raw/gtfs/stops'
tblproperties ('skip.header.line.count'='1');

create external table if not exists raw_gtfs_routes(
  route_id string, agency_id string, route_short_name string, route_long_name string,
  route_type string, route_color string, route_text_color string)
row format serde 'org.apache.hadoop.hive.serde2.OpenCSVSerde'
stored as textfile
location '/datalake/raw/gtfs/routes'
tblproperties ('skip.header.line.count'='1');

create external table if not exists raw_gtfs_trips(
  route_id string, service_id string, trip_id string, shape_id string,
  trip_headsign string, direction_id string, block_id string, trip_short_name string)
row format serde 'org.apache.hadoop.hive.serde2.OpenCSVSerde'
stored as textfile
location '/datalake/raw/gtfs/trips'
tblproperties ('skip.header.line.count'='1');

create external table if not exists raw_gtfs_stop_times(
  trip_id string, arrival_time string, departure_time string, stop_id string,
  stop_sequence string, stop_headsign string, pickup_type string,
  drop_off_type string, shape_dist_traveled string)
row format serde 'org.apache.hadoop.hive.serde2.OpenCSVSerde'
stored as textfile
location '/datalake/raw/gtfs/stop_times'
tblproperties ('skip.header.line.count'='1');

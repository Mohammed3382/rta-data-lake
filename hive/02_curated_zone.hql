-- 02_curated_zone.hql
-- Cleansed journeys (output of the MapReduce job) and the star schema
-- in the curated zone. Curated tables are stored as ORC.

use rta_lake;
set hive.exec.dynamic.partition=true;
set hive.exec.dynamic.partition.mode=nonstrict;

-- cleansed zone: journeys built by nol_clean_mapper.py / nol_journey_reducer.py
create external table if not exists cln_nol_journeys(
  card_id string, card_type string, mode string,
  entry_ts string, exit_ts string,
  origin_stop string, dest_stop string,
  duration_min double, fare_aed double, travel_date string)
row format delimited fields terminated by ','
stored as textfile
location '/datalake/cleansed/nol_journeys';

-- dimension: station (cleaned names from GTFS + which line serves it)
create table if not exists dim_station(
  stop_id string, station_name string, line string, mode string,
  latitude double, longitude double)
stored as orc;

insert overwrite table dim_station
select s.stop_id,
       trim(regexp_replace(regexp_replace(regexp_replace(regexp_replace(
            s.stop_name, '\\s+', ' '),
            '\\(Green Line ?\\)', ''),
            '(?i)\\s*metro\\s*station\\s*\\d*$', ''),
            '(?<=[a-z])\\d+$', '')) as station_name,
       l.line, l.mode,
       cast(s.stop_lat as double), cast(s.stop_lon as double)
from raw_gtfs_stops s
join (select st.stop_id,
             concat_ws('/', sort_array(collect_set(
               case when r.route_short_name like 'MRed%' then 'Red'
                    when r.route_short_name = 'MGrn' then 'Green'
                    else 'Tram' end))) as line,
             max(case when r.route_type = '1' then 'METRO' else 'TRAM' end) as mode
      from raw_gtfs_stop_times st
      join raw_gtfs_trips t  on st.trip_id = t.trip_id
      join raw_gtfs_routes r on t.route_id = r.route_id
      where r.route_type in ('0', '1')
      group by st.stop_id) l
on s.stop_id = l.stop_id;

-- dimension: card type
create table if not exists dim_card_type(
  card_type string, description string, fare_rule string)
stored as orc;

truncate table dim_card_type;   -- so the script can be run again without duplicate rows
insert into table dim_card_type values
  ('SILVER', 'Silver nol card (anonymous)', 'standard fare'),
  ('BLUE', 'Blue nol card (personal)', 'standard fare'),
  ('GOLD', 'Gold nol card', 'double fare, Gold class'),
  ('RED', 'Red nol ticket (paper)', 'standard fare plus ticket cost'),
  ('CONCESSION', 'Students, seniors, people of determination', '50% discount');

-- fact: one row per journey, partitioned by day
create table if not exists fact_journey(
  card_id string, card_type string, mode string,
  origin_stop string, dest_stop string,
  entry_ts timestamp, exit_ts timestamp, entry_hour int,
  duration_min double, fare_aed decimal(6,2))
partitioned by (travel_date string)
stored as orc;

-- travel_date is taken from entry_ts because the MapReduce output has a tab at the end of each line
insert overwrite table fact_journey partition (travel_date)
select card_id, card_type, mode, origin_stop, dest_stop,
       cast(entry_ts as timestamp), cast(exit_ts as timestamp),
       hour(entry_ts), duration_min, cast(fare_aed as decimal(6,2)),
       substr(entry_ts, 1, 10)
from cln_nol_journeys;

-- dimension: date (built from the days we actually have)
create table if not exists dim_date(
  travel_date string, day_name string, is_weekend string, week_of_year int)
stored as orc;

insert overwrite table dim_date
select d, date_format(d, 'EEEE'),
       case when date_format(d, 'u') in ('6', '7') then 'Weekend' else 'Weekday' end,
       weekofyear(d)
from (select distinct travel_date as d from fact_journey) x;

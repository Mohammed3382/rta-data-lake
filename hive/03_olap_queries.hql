-- 03_olap_queries.hql
-- Sample analysis on the curated star schema.

use rta_lake;

-- Q1 journeys and fare revenue per day
select d.travel_date, d.day_name, d.is_weekend,
       count(*) as journeys, sum(f.fare_aed) as revenue_aed
from fact_journey f join dim_date d on f.travel_date = d.travel_date
group by d.travel_date, d.day_name, d.is_weekend
order by d.travel_date;

-- Q2 ten busiest origin stations for the week
select s.station_name, s.line, count(*) as journeys
from fact_journey f join dim_station s on f.origin_stop = s.stop_id
group by s.station_name, s.line
order by journeys desc
limit 10;

-- Q3 hourly profile, weekday vs weekend (average per day)
select f.entry_hour, d.is_weekend,
       round(count(*) / count(distinct f.travel_date), 0) as avg_journeys
from fact_journey f join dim_date d on f.travel_date = d.travel_date
group by f.entry_hour, d.is_weekend
order by f.entry_hour, d.is_weekend;

-- Q4 roll-up: revenue by line and station, with subtotals per line and a grand total
select s.line, s.station_name, sum(f.fare_aed) as revenue_aed, count(*) as journeys
from fact_journey f join dim_station s on f.origin_stop = s.stop_id
where f.mode = 'METRO'
group by s.line, s.station_name with rollup
order by s.line, revenue_aed desc;

-- Q5 cube: card type by weekday/weekend
select f.card_type, d.is_weekend, count(*) as journeys, round(avg(f.fare_aed), 2) as avg_fare
from fact_journey f join dim_date d on f.travel_date = d.travel_date
group by f.card_type, d.is_weekend with cube;

-- Q6 most common origin -> destination pairs
select o.station_name as origin, ds.station_name as destination, count(*) as journeys,
       round(avg(f.duration_min), 1) as avg_minutes
from fact_journey f
join dim_station o  on f.origin_stop = o.stop_id
join dim_station ds on f.dest_stop = ds.stop_id
group by o.station_name, ds.station_name
order by journeys desc
limit 10;

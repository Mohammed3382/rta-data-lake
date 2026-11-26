# generate_nol_taps.py
# Generates one week of synthetic Nol tap records (5 to 11 Oct 2026).
# Stations come from the real RTA GTFS feed, daily volumes are scaled to the
# RTA's published 2025 ridership, and a small share of records get the errors
# a real fare system has: duplicates, missing tap outs, old date format,
# missing stop codes and staff test cards.
#
# usage: python3 generate_nol_taps.py <gtfs_folder> <output_folder>
# works on Python 3.5 (the course VM) and newer

import collections
import csv
import datetime as dt
import functools
import hashlib
import os
import random
import re
import sys
from bisect import bisect
from itertools import accumulate

if len(sys.argv) != 3:
    sys.exit("usage: python3 generate_nol_taps.py <gtfs_folder> <output_folder>")
G, OUT = sys.argv[1], sys.argv[2]
random.seed(312)   # fixed seed so the same week can be generated again


def choices(population, weights, k=1):
    # same algorithm as random.choices (Python 3.9+), written out because the
    # VM has Python 3.5. With the same seed it gives exactly the same data.
    cum = list(accumulate(weights))
    total = cum[-1] + 0.0
    hi = len(cum) - 1
    return [population[bisect(cum, random.random() * total, 0, hi)] for _ in range(k)]


def read_gtfs(name):
    with open('{0}/{1}.txt'.format(G, name), encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))


def canon(n):
    # same cleaning rules as dim_station in hive/02_curated_zone.hql
    n = re.sub(r'\s+', ' ', n).strip()
    n = re.sub(r'\(Green Line ?\)', '', n, flags=re.I)
    n = re.sub(r'\s*Metro\s*station\s*\d*$', '', n, flags=re.I)
    n = re.sub(r'(?<=[a-z])\d+$', '', n)
    return re.sub(r'\s+', ' ', n).strip()


# metro (route_type 1) and tram (route_type 0) only
routes = {r['route_id']: r for r in read_gtfs('routes') if r['route_type'] in ('0', '1')}
trips = collections.defaultdict(list)
for t in read_gtfs('trips'):
    if t['route_id'] in routes:
        trips[t['route_id']].append(t['trip_id'])
want = {tid for l in trips.values() for tid in l}
st = collections.defaultdict(list)
for r in read_gtfs('stop_times'):
    if r['trip_id'] in want:
        st[r['trip_id']].append((int(r['stop_sequence']), r['stop_id']))
stops = {s['stop_id']: s for s in read_gtfs('stops')}
# station order on each line, taken from its longest trip
lines, sid, mode = {}, {}, {}
for rid, r in routes.items():
    best = max(trips[rid], key=lambda t: len(st[t]))
    seq = []
    for _, s in sorted(st[best]):
        c = canon(stops[s]['stop_name'])
        seq.append(c)
        sid.setdefault(c, s)
        mode[c] = 'TRAM' if r['route_type'] == '0' else 'METRO'
    lines[r['route_short_name']] = seq
adj = collections.defaultdict(set)
for seq in lines.values():
    for a, b in zip(seq, seq[1:]):
        adj[a].add(b)
        adj[b].add(a)


@functools.lru_cache(maxsize=None)
def hops(a, b):
    # number of stops between two stations (breadth first search), used for trip time and fare
    seen = {a: 0}
    q = [a]
    for x in q:
        if x == b:
            return seen[x]
        for y in adj[x]:
            if y not in seen:
                seen[y] = seen[x] + 1
                q.append(y)
    return 1


metro = [s for s in sid if mode[s] == 'METRO']
tram = [s for s in sid if mode[s] == 'TRAM']
# weights for the busiest stations, everything else gets 1
busy = {'BurJuman': 6, 'Union': 6, 'Mall of the Emirates': 5, 'Burj Khalifa/ Dubai Mall': 5, 'Al Rigga': 4, 'City Centre Deira': 4,
        'Business Bay': 4, 'Dubai Internet City': 3, 'Ibn Battuta': 3, 'Sharaf DG': 3, 'Al Nahda': 3, 'Stadium': 3, 'Al Qusais': 3,
        'Airport Terminal 1': 3, 'Airport Terminal 3': 4, 'Financial Centre': 3, 'Emirates Towers': 3, 'World Trade Centre': 2,
        'Baniyas Square': 3, 'Al Ghubaiba': 3, 'Jumeirah Lakes Towers': 3, 'DMCC': 3, 'Dubai Marina': 3, 'Jumeirah Beach Residence': 2}
w_metro = [busy.get(s, 1) for s in metro]
w_tram = [busy.get(s, 1) for s in tram]
# share of trips per hour, weekday (WD) and weekend (WE)
WD = [0.2, 0.1, 0, 0, 0, 0.6, 2.2, 6.8, 8.9, 6.1, 4.2, 3.9, 4.1, 4.3, 4.6, 5.2, 6.4, 8.4, 8.8, 7.1, 5.6, 4.4, 3.2, 1.6]
WE = [1.0, 0.5, 0, 0, 0, 0.3, 0.9, 2.0, 3.1, 3.9, 4.6, 5.3, 5.9, 6.1, 6.0, 6.2, 6.6, 7.2, 7.6, 7.8, 7.3, 6.2, 4.6, 2.9]
types = ['SILVER'] * 55 + ['BLUE'] * 25 + ['RED'] * 10 + ['GOLD'] * 5 + ['CONCESSION'] * 5


def fare(h, t):
    # three fare zones by number of stops, adjusted by card type
    z = 0 if h <= 4 else (1 if h <= 11 else 2)
    f = [3.0, 5.0, 7.5][z]
    if t == 'GOLD':
        f *= 2
    elif t == 'CONCESSION':
        f /= 2
    elif t == 'RED':
        f += 1.0
    return round(f, 2)


POOL = 1400000   # number of different cards
cards = [hashlib.sha1('nolcard{0}'.format(i).encode()).hexdigest()[:12] for i in range(POOL)]
ctype = [random.choice(types) for _ in range(POOL)]
start = dt.date(2026, 10, 5)
os.makedirs(OUT, exist_ok=True)
txn = 0
stats = collections.Counter()
hrs = list(range(24))
for d in range(7):
    day = start + dt.timedelta(days=d)
    weekend = day.weekday() >= 5
    target_metro = int(807000 * (0.82 if weekend else 1.08) * random.uniform(0.97, 1.03))
    target_tram = int(27100 * (1.15 if weekend else 0.95))
    prof = WE if weekend else WD
    fn = '{0}/nol_taps_{1:%Y%m%d}.csv'.format(OUT, day)
    with open(fn, 'w', newline='') as f:
        w = f.write
        w('txn_id,card_id,card_type,tap_ts,stop_id,gate_id,tap_type,fare_aed,mode\n')
        for md, target, pool, wts in (('METRO', target_metro, metro, w_metro), ('TRAM', target_tram, tram, w_tram)):
            made = 0
            while made < target:
                ci = random.randrange(POOL)
                card, t = cards[ci], ctype[ci]
                k = choices([1, 2, 3], [0.3, 0.6, 0.1])[0]
                times = sorted(choices(hrs, prof, k=k))
                cur, last_end = None, None
                for hr in times:
                    o = cur or choices(pool, wts)[0]
                    dd = choices(pool, wts)[0]
                    while dd == o:
                        dd = choices(pool, wts)[0]
                    h = hops(o, dd)
                    dur = 3 + h * 2.4 + (5 if md == 'METRO' and h > 8 else 0) + random.uniform(-1, 4)
                    ts = dt.datetime.combine(day, dt.time(hr)) + dt.timedelta(seconds=random.randrange(3600))
                    if last_end and ts < last_end + dt.timedelta(minutes=20):
                        ts = last_end + dt.timedelta(minutes=random.randrange(20, 240))
                    te = ts + dt.timedelta(minutes=dur)
                    if te.date() != day:
                        break
                    last_end, cur = te, dd
                    so, sd = sid[o], sid[dd]
                    rin = ['T{0:011d}'.format(txn), card, t, ts.strftime('%Y-%m-%d %H:%M:%S'), so,
                           'G{0}-{1:02d}'.format(so, random.randint(1, 12)), 'IN', '0.00', md]
                    txn += 1
                    rout = ['T{0:011d}'.format(txn), card, t, te.strftime('%Y-%m-%d %H:%M:%S'), sd,
                            'G{0}-{1:02d}'.format(sd, random.randint(1, 12)), 'OUT', '{0:.2f}'.format(fare(h, t)), md]
                    txn += 1
                    # add errors: 0.6% no tap out, 0.4% old date format, 0.2% no stop code, 0.4% duplicates
                    r = random.random()
                    if r < 0.006:
                        rout = None
                        stats['no_out'] += 1
                    elif r < 0.010:
                        rin[3] = ts.strftime('%d/%m/%Y %H:%M')
                        stats['bad_ts'] += 1
                    elif r < 0.012:
                        rin[4] = ''
                        stats['no_stop'] += 1
                    w(','.join(rin) + '\n')
                    if random.random() < 0.004:
                        w(','.join(rin) + '\n')
                        stats['dup'] += 1
                    if rout:
                        w(','.join(rout) + '\n')
                    made += 1
            if md == 'METRO':   # staff test cards at night
                for i in range(random.randint(40, 90)):
                    s = sid[random.choice(metro)]
                    w('T{0:011d},TEST{1},STAFF,{2} 03:{3}:{4},{5},G{5}-01,IN,0.00,METRO\n'.format(
                        txn, random.randint(1000, 9999), day, random.randint(10, 59), random.randint(10, 59), s))
                    txn += 1
                    stats['test'] += 1
    print(fn, target_metro, target_tram, os.path.getsize(fn) // 1000000, 'MB', flush=True)
print(dict(stats))

# station lookup file, used to check the generator against the GTFS feed
with open(os.path.join(os.path.dirname(OUT), 'station_ref.csv'), 'w', newline='') as f:
    cw = csv.writer(f)
    cw.writerow(['canon', 'stop_id', 'mode', 'lines'])
    for c, s in sid.items():
        cw.writerow([c, s, mode[c], '|'.join(l for l, seq in lines.items() if c in seq)])

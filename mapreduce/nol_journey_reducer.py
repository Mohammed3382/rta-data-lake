#!/usr/bin/env python3
# nol_journey_reducer.py
# Gets all taps of one card together (Hadoop sorts by card_id).
# Removes duplicate taps, sorts by time and pairs every IN with the next OUT.
# Output (CSV): card_id,card_type,mode,entry_ts,exit_ts,origin_stop,dest_stop,duration_min,fare_aed,travel_date

import sys
from datetime import datetime

MAX_TRIP_MIN = 180   # a metro trip longer than 3 hours is not a real trip


counts = {}


def counter(name, n=1):
    # Hadoop reads "reporter:counter:..." lines from stderr. We add them up
    # here and report once at the end instead of once per record.
    counts[name] = counts.get(name, 0) + n


def report():
    for name, n in counts.items():
        sys.stderr.write("reporter:counter:NOL Cleansing,{0},{1}\n".format(name, n))


def flush(card, raw_taps):
    taps = sorted(set(raw_taps))       # set() drops exact duplicate taps
    dups = len(raw_taps) - len(taps)
    if dups:
        counter("Duplicate taps removed", dups)
    open_in = None
    for t in taps:
        ts, stop, tap, fare, ctype, mode = t
        if tap == "IN":
            if open_in is not None:
                counter("Missing tap out")
            open_in = t
        elif tap == "OUT" and open_in is not None:
            t_in = datetime.strptime(open_in[0], "%Y-%m-%d %H:%M:%S")
            t_out = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
            mins = (t_out - t_in).total_seconds() / 60.0
            if 0 < mins <= MAX_TRIP_MIN:
                print(",".join([card, ctype, mode, open_in[0], ts, open_in[1], stop,
                                "{0:.1f}".format(mins), fare, open_in[0][:10]]))
                counter("Journeys built")
            else:
                counter("Rejected long or negative trip")
            open_in = None
        else:
            counter("Tap out without tap in")
    if open_in is not None:
        counter("Missing tap out")


current, card_taps = None, []
for line in sys.stdin:
    parts = line.rstrip("\n").split("\t")
    if len(parts) != 2:
        continue
    card, value = parts
    if current is not None and card != current:
        flush(current, card_taps)
        card_taps = []
    current = card
    card_taps.append(tuple(value.split("|")))

if current is not None:
    flush(current, card_taps)

report()

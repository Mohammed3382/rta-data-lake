#!/usr/bin/env python3
# nol_clean_mapper.py
# Reads raw Nol tap records (CSV) from the raw zone.
# Checks each record and sends good taps to the reducer, grouped by card.
# Output: card_id <TAB> tap_ts|stop_id|tap_type|fare|card_type|mode

import sys
from datetime import datetime


counts = {}


def counter(name, n=1):
    # Hadoop reads "reporter:counter:..." lines from stderr. We add them up
    # here and report once at the end instead of once per record.
    counts[name] = counts.get(name, 0) + n


def report():
    for name, n in counts.items():
        sys.stderr.write("reporter:counter:NOL Cleansing,{0},{1}\n".format(name, n))


def fix_ts(ts):
    # most gates send yyyy-mm-dd hh:mm:ss, some older gates send dd/mm/yyyy hh:mm
    for fmt in ("%Y-%m-%d %H:%M:%S", "%d/%m/%Y %H:%M"):
        try:
            return datetime.strptime(ts, fmt).strftime("%Y-%m-%d %H:%M:%S"), fmt
        except ValueError:
            pass
    return None, None


for line in sys.stdin:
    cols = line.strip().split(",")
    if len(cols) != 9 or cols[0] == "txn_id":
        continue
    txn, card, ctype, ts, stop, gate, tap, fare, mode = cols

    if card.startswith("TEST") or ctype == "STAFF":
        counter("Rejected test cards")
        continue
    if stop == "":
        counter("Rejected missing stop")
        continue
    clean_ts, fmt = fix_ts(ts)
    if clean_ts is None:
        counter("Rejected bad timestamp")
        continue
    if fmt != "%Y-%m-%d %H:%M:%S":
        counter("Fixed old gate timestamp")
    if tap not in ("IN", "OUT"):
        counter("Rejected bad tap type")
        continue

    counter("Valid taps")
    print("{0}\t{1}|{2}|{3}|{4}|{5}|{6}".format(card, clean_ts, stop, tap, fare, ctype, mode))

report()

#!/bin/bash
# One-time setup on the BigDataVM: downloads the GTFS feed and generates the Nol taps.
# usage: bash setup.sh

cd "$(dirname "$0")"
mkdir -p ~/rta_data/gtfs

echo "--- downloading the RTA GTFS feed"
wget -q -O ~/rta_data/gtfs/latest.zip https://files.mobilitydatabase.org/mdb-3359/latest.zip
python3 -m zipfile -e ~/rta_data/gtfs/latest.zip ~/rta_data/gtfs/

echo "--- generating one week of Nol taps (takes a few minutes)"
python3 data_generator/generate_nol_taps.py ~/rta_data/gtfs ~/rta_data/nol

chmod +x run/*.sh
echo "--- done. Now run the scripts in run/ in order, starting with run/00_start_services.sh"

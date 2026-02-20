import requests
import sqlite3
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from google.transit import gtfs_realtime_pb2
import os
import sys

# API Layer

GTFS_DB = "gtfs.db"
URL = "https://api.opendata.transport.vic.gov.au/opendata/public-transport/gtfs/realtime/v1/metro/trip-updates"

KEY_FILE = "api_key.txt"

def load_api_key():
    '''
    If "api_key.txt" doesn't exist, create it and exit
    Otherwise, return key
    '''
    key_placeholder = "PUT_YOUR_API_KEY_HERE"
    if not os.path.exists(KEY_FILE): 
        with open(KEY_FILE, "w") as f:  f.write(key_placeholder)
    else:
        with open(KEY_FILE, "r") as f:  key = f.read().strip()
    
    status = False if not key or key == key_placeholder else True
    return key, status

API_KEY, status = load_api_key()

HEADERS = { "KeyId": API_KEY }
MELBOURNE = ZoneInfo("Australia/Melbourne") # GTFS uses GMT+0, default to Melbourne Timezone

SCHEDULE_ENUM = {   # Enum used in GTFS
    0: "SCHEDULED",
    1: "ADDED",
    2: "UNSCHEDULED",
    3: "CANCELED",
    4: "DUPLICATED",
    5: "DELETED"
}

# =====================
# UTILITY FUNCTIONS
# =====================
def load_stop_lookup():
    '''
    Uses the dataset to lookup corresponding stop_id to readable Station Name.
    '''
    conn = sqlite3.connect(GTFS_DB)
    cur = conn.cursor()
    cur.execute("SELECT stop_id, stop_name, platform_code FROM stops")
    lookup = {
        stop_id: {"name": stop_name, "platform": platform_code}
        for stop_id, stop_name, platform_code in cur.fetchall()
    }
    conn.close()
    return lookup

def load_scheduled_times(trip_id):
    '''
    Return scheduled time based on the GTFS datasets with operational hours,
    where same operation day over midnight is displayed beyond 24:00 even it is a new day
    (e.g. 01:02 of 23/01 will be 25:02 22/01), display will unitfy to show 00:00 - 23:59
    '''
    conn = sqlite3.connect(GTFS_DB)
    cur = conn.cursor()
    cur.execute("SELECT stop_id, arrival_time FROM stop_times WHERE trip_id = ?", (trip_id,))
    schedule = {}
    service_day = datetime.now(MELBOURNE).replace(hour=0, minute=0, second=0, microsecond=0)
    for stop_id, arrival_time in cur.fetchall():
        if not arrival_time:
            continue
        h, m, s = map(int, arrival_time.split(":"))
        total_seconds = h * 3600 + m * 60 + s
        schedule[stop_id] = service_day + timedelta(seconds=total_seconds)
    conn.close()
    return schedule

STOP_LOOKUP = load_stop_lookup()

def calculate_delay(rt_time, sched_time):
    if not rt_time or not sched_time: return None
    delay_min = int((rt_time - sched_time).total_seconds() / 60)
    return delay_min

# =====================
# MAIN FUNCTIONS
# =====================
def return_trip_realtime(trip_ids, station_name, feed):
    """
    Returns simplified realtime info for multiple trips at a given station.
    Returns a dict: {trip_id: list of dicts per stop with keys: relationship, scheduled, realtime, delay}
    """
    result = {}
    for trip_id in trip_ids:
        schedule_map = load_scheduled_times(trip_id)
        trip_found = False
        trip_stops = []

        for entity in feed.entity:
            if not entity.HasField("trip_update"):
                continue
            tu = entity.trip_update
            if tu.trip.trip_id != trip_id:
                continue

            trip_found = True
            for stu in tu.stop_time_update:
                stop_info = STOP_LOOKUP.get(stu.stop_id, {})
                stop_name_real = stop_info.get("name", stu.stop_id)
                if station_name.lower() not in stop_name_real.lower():
                    continue

                # Realtime time
                rt_time = None
                if stu.HasField("arrival") and stu.arrival.time:        rt_time = datetime.fromtimestamp(stu.arrival.time, tz=timezone.utc).astimezone(MELBOURNE)
                elif stu.HasField("departure") and stu.departure.time:  rt_time = datetime.fromtimestamp(stu.departure.time, tz=timezone.utc).astimezone(MELBOURNE)

                sched_time = schedule_map.get(stu.stop_id)
                sched_str = sched_time.strftime("%H:%M") if sched_time else "N/A"
                rt_str = rt_time.strftime("%H:%M") if rt_time else "N/A"

                relationship = SCHEDULE_ENUM.get(stu.schedule_relationship, "UNKNOWN") if stu.HasField("schedule_relationship") else "UNKNOWN"
                delay_int = calculate_delay(rt_time, sched_time)

                trip_stops.append({
                    "relationship": relationship,
                    "scheduled": sched_str,
                    "realtime": rt_str,
                    "delay": delay_int
                })

            break  # stop after first matching trip update

        result[trip_id] = trip_stops if trip_found else []

    return result


def enquiry(station_name: str, trip_id_lst):
    '''
    Takes User input and Real Time info into the format for gtfs_query.py
    '''
    station_name_input = station_name.strip()
    trip_ids_input = [tid.strip() for tid in trip_id_lst if tid.strip()]

    response = requests.get(URL, headers=HEADERS)
    if response.status_code != 200:
        return None

    feed = gtfs_realtime_pb2.FeedMessage()
    feed.ParseFromString(response.content)

    # Get realtime info
    trips_data = return_trip_realtime(trip_ids_input, station_name_input, feed)

    return trips_data
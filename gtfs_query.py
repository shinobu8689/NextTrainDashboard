from collections import defaultdict
import sqlite3
import csv
from datetime import datetime, timedelta
import os
import time
from fastapi import FastAPI
import current_trips

# Main Logic

app = FastAPI()

DB_FILE = "gtfs.db"
GTFS_PATH = "gtfs_metro_trains/"

FILES = {
    "stops": "stops.txt",
    "stop_times": "stop_times.txt",
    "trips": "trips.txt",
    "routes": "routes.txt",
    "calendar": "calendar.txt",
}

CITY_STATIONS = [
    "Flagstaff Station",
    "Melbourne Central Station",
    "Parliament Station",
    "Southern Cross Station"
]

def find_next_trip_in_block(conn, block_id, current_trip_id):
    '''
    find the next trip of the same block (same physical train)
    '''
    if not block_id:
        return None

    q = """
    SELECT t.trip_headsign, MIN(st.departure_time), t.direction_id
    FROM trips t
    JOIN stop_times st ON t.trip_id = st.trip_id
    WHERE t.block_id = ?
      AND t.trip_id != ?
    GROUP BY t.trip_id
    ORDER BY MIN(st.departure_time)
    LIMIT 1
    """
    return conn.execute(q, (block_id, current_trip_id)).fetchone()

def time_str_to_min(time_str):
    '''
    parse time string into minutes with difference formats
    '''
    parts = list(map(int, time_str.split(":")))
    if len(parts) == 2:
        h, m = parts
        s = 0
    elif len(parts) == 3:
        h, m, s = parts
    else:
        raise ValueError(f"Invalid time string: {time_str}")
    return h * 60 + m

def minutes_until(departure_time_str, now_str):
    """
    Handles both GTFS (24:xx, 25:xx) and realtime (00:xx next-day)
    """
    dep_parts = list(map(int, departure_time_str.split(":")))
    now_parts = list(map(int, now_str.split(":")))

    dep_h, dep_m = dep_parts[0], dep_parts[1]
    now_h, now_m = now_parts[0], now_parts[1]

    dep_total = dep_h * 60 + dep_m
    now_total = now_h * 60 + now_m

    # assume it's next day if departure hour < 3 AND current hour >= 21
    if dep_h < 3 and now_h >= 21: dep_total += 24 * 60
    return dep_total - now_total

def format_time_display(time_str):
    """
    Format HH:MM:SS or HH:MM (possibly >24h) into standard 00:00–23:59 time.
    """
    parts = list(map(int, time_str.split(":")))
    
    if len(parts) == 3:
        h, m, s = parts
    elif len(parts) == 2:
        h, m = parts
        s = 0
    else:
        raise ValueError(f"Invalid time format: {time_str}")

    total_minutes = h * 60 + m
    total_minutes %= 24 * 60  # wrap around 24h

    new_h = total_minutes // 60
    new_m = total_minutes % 60

    return f"{new_h:02d}:{new_m:02d}"


"""
 to be converted feature from terminal ver, might implement later
 get_next_stops()
 render_next_stops()
"""
 
def get_next_stops(conn, trip_id, current_seq):
    '''
    using the trip id, look for the remaining stops based on schedule data
    '''
    now_min = time_str_to_min(now)

    q = f"""
    SELECT s.stop_name, st.arrival_time
    FROM stop_times st
    JOIN stops s ON st.stop_id = s.stop_id
    WHERE st.trip_id = '{trip_id}'
      AND st.stop_sequence + 0 > {current_seq}
    """
    cursor = conn.execute(q)
    # filter manually using minutes
    result = []
    for stop_name, arr_time in cursor.fetchall():
        arr_min = time_str_to_min(arr_time)
        if arr_min >= now_min:
            result.append((stop_name, arr_time))
    return result

def render_next_stops(next_stops): 
    '''
    show the route and all stopping stations following the timetable.

    next_stops = get_next_stops(conn, trip_id, stop_seq)
    if next_stops:  render_next_stops(next_stops)
    else:           print("└ Terminates")

    '''
    max_rows = 7
    total_stops = len(next_stops)

    # calculate required columns
    columns = [next_stops[i:i + max_rows] for i in range(0, total_stops, max_rows)]

    # calculate the column widths
    col_widths = []
    for col in columns:
        max_len = max(len(' '.join(name.split()[:-1])) for name, _ in col)
        col_widths.append(max_len)

    # calculate required rows
    max_print_rows = max(len(col) for col in columns)

    # print
    for row in range(max_print_rows):
        row_str = ""
        for c, col in enumerate(columns):
            if row < len(col):
                name, arr = col[row]

                # Last stop in last column → └
                if (row == len(col) - 1) and (c == len(columns) - 1):   branch = "└"
                else:   branch = "├"

                left_name = ' '.join(name.split()[:-1])
                row_str += f"{branch} {left_name.ljust(col_widths[c])}   "
            else:
                row_str += " " * (col_widths[c] + 3)

        print(row_str.rstrip())

    print()

def organise(station_name, trains, max_per_platform=3):
    """
    General Rules:
    - Replacement bus platform = -1
    - Limit results to max_per_platform per platform (dafault 3)

    Town Hall Special Rules as it shows duplicate entries when it changes trips:
    - P1 → direction_id = 1
    - P2 → direction_id = 0
    """

    organised = []

    # Normalize platform
    for t in trains:
        if not t["platform"] or not str(t["platform"]).isdigit():   t["platform"] = -1          # Replacement bus
        else:                                                       t["platform"] = int(t["platform"])

        if station_name == "Town Hall Station":
            if t["platform"] == 1 and t["direction_id"] == "1":     organised.append(t)
            elif t["platform"] == 2 and t["direction_id"] == "0":   organised.append(t)
        else:   organised.append(t)

    # Limit entries per platform
    limited = []
    grouped = defaultdict(list)
    for t in organised:         grouped[t["platform"]].append(t)
    for platform in grouped:    limited.extend(grouped[platform][:max_per_platform])

    return limited

def get_station_data(station_name, conn):

    now = datetime.now().strftime("%H:%M:%S")
    five_mins_ago = (datetime.now() - timedelta(minutes=3)).strftime("%H:%M:%S")
    weekday = datetime.now().strftime("%A").lower()
    today = datetime.now().strftime("%Y%m%d")

    query = f"""
    WITH ranked AS (
        SELECT 
            r.route_color,
            s.platform_code,
            t.trip_headsign,
            st.departure_time,
            t.trip_id,
            st.stop_sequence,
            t.block_id,
            t.direction_id,
            s.stop_name,

        ROW_NUMBER() OVER (
            PARTITION BY s.platform_code
            ORDER BY st.departure_time
        ) AS rn

        FROM stop_times st
        JOIN stops s ON st.stop_id = s.stop_id
        JOIN trips t ON st.trip_id = t.trip_id
        JOIN routes r ON t.route_id = r.route_id
        JOIN calendar c ON t.service_id = c.service_id

        WHERE s.parent_station = (
            SELECT stop_id
            FROM stops
            WHERE stop_name LIKE '%{station_name}%'
            AND location_type = '1'
        )
        AND s.stop_name LIKE '%{station_name}%'
        AND LOWER(t.trip_headsign) NOT LIKE LOWER('%{station_name}%')
        AND c.start_date <= '{today}'
        AND c.end_date >= '{today}'
        AND c.{weekday} = '1'
        AND st.departure_time >= '{five_mins_ago}'
    )

    SELECT
        route_color,
        platform_code,
        trip_headsign,
        departure_time,
        trip_id,
        block_id,
        direction_id,
        stop_name
    FROM ranked
    WHERE rn <= 12
    ORDER BY CAST(platform_code AS INTEGER) ASC, departure_time;
        """

    cursor = conn.execute(query)
    rows = cursor.fetchall()
    station_name = rows[-1][-1] if rows else "No results found"

    trip_lst = [each[4] for each in rows]                       # Get the list of trips to enquiry RT status
    response = current_trips.enquiry(station_name, trip_lst)

    trains = []

    for each in rows:
        route_color, platform, headsign, dep_time, trip_id, block_id, direction_id, stop_name = each

        # Showing dest for trip passing city's station if inbound trains heading to Flinders Street first
        if direction_id == "1" and any(word in station_name for word in CITY_STATIONS):
            next_trip = find_next_trip_in_block(conn, block_id, trip_id)
            if next_trip:   headsign = f"{next_trip[0]}"

        # Default scheduled time calculations
        mins = minutes_until(dep_time, now)
        dep_time_display = format_time_display(dep_time)

        # Check with realtime response
        delay_int = 0
        trip_relationship = ""
        if response and trip_id in response and response[trip_id]:
            stop_data = response[trip_id][0]  # Only one stop matching station_name
            trip_relationship = response[trip_id][0]["relationship"]
            new_dep_time = format_time_display(stop_data["realtime"])
            delay_int = stop_data["delay"]

            # Calculate mins until new departure
            mins = minutes_until(new_dep_time, now)
            if dep_time_display == new_dep_time:    dep_time_display = f"{new_dep_time}"
            else:                                   dep_time_display = f"{dep_time_display} → {new_dep_time}"


        train_data = {
            "route_color": route_color,
            "platform": platform,
            "destination": headsign,
            "scheduled_time": dep_time_display,
            "minutes_until": mins,
            "delay_minutes": delay_int,
            "status": trip_relationship or "SCHEDULED",
            "trip_id": trip_id,
            "block_id": block_id,
            "direction_id": direction_id
        }

        trains.append(train_data)

    trains = sorted(trains, key=lambda t: t["minutes_until"])
    trains = organise(station_name, trains)
    trains.sort(key=lambda t: (int(t['platform']), t['minutes_until']))

    return {
        "station": stop_name,
        "current_time": now,
        "trains": trains
    }


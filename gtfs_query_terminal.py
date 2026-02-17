import sqlite3
import csv
from datetime import datetime, timedelta
import os
import time



import current_trips

DB_FILE = "gtfs.db"
GTFS_PATH = "gtfs_metro_trains/"

'''
TODO:
Code refactor for future web-based GUI with JavaScript instead of terminal.
To add support for multi-station enquiry in terminal.
Determine the viability auto updating dataset from Transport Victoria.
Simplify setup process.
Implement option.txt for default stations and other settings.
'''


FILES = {
    "stops": "stops.txt",
    "stop_times": "stop_times.txt",
    "trips": "trips.txt",
    "routes": "routes.txt",
    "calendar": "calendar.txt",
}

# Trains from the city might switch to another destination where they loop until arriving at Flinders
CITY_STATIONS = [
    "Flagstaff Station",
    "Melbourne Central Station",
    "Parliament Station",
    "Southern Cross Station"
]

def colour_text(hex_code, text):
    '''
    FOR TERMINAL
    Print text with HEX colour code, where it gets translated into rgb value for terminal.
    '''
    r, g, b = (int(hex_code.lstrip("#")[i:i+2], 16) for i in (0, 2, 4))
    return f"\033[38;2;{r};{g};{b}m{text}\033[0m"

def load_table(conn, table, filename):
    '''
    create a db file based on txt to use SQLite
    '''
    with open(GTFS_PATH + filename, encoding="utf-8") as f:
        reader = csv.reader(f)
        headers = next(reader)

        conn.execute(f"DROP TABLE IF EXISTS {table}")
        conn.execute(f"CREATE TABLE {table} ({','.join(h + ' TEXT' for h in headers)})")
        for row in reader: conn.execute(f"INSERT INTO {table} VALUES ({','.join('?' * len(row))})", row)
    conn.commit()

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

def minutes_until(departure_time_str):
    '''
    compute the time differences between scheduled time and actual time
    '''
    dep_min = time_str_to_min(departure_time_str)
    now_min = time_str_to_min(now)

    diff = dep_min - now_min
    return diff

def format_time_display(time_str):
    '''
    Format HH:MM:SS, possibly >24, into HH:MM
    '''
    h, m, s = map(int, time_str.split(":"))
    return f"{h:02d}:{m:02d}"

def render_next_stops(next_stops):
    '''
    show the route and all stopping stations following the timetable.
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



def main(input_string, conn):

    # debug prompt input option checker
    show_stopping_detail = "*" in input_string
    station_name = input_string.replace("*", "")
    show_debug = input_string[-2:] == " d"
    if show_debug: station_name = input_string[:-2]



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
        stop_sequence,
        block_id,
        direction_id,
        stop_name
    FROM ranked
    WHERE rn <= 8
    ORDER BY CAST(platform_code AS INTEGER) ASC, departure_time;
        """

    cursor = conn.execute(query)
    rows = cursor.fetchall()
    station_name = rows[-1][-1] if rows else "No results found"


    print(f"\n🚇 {station_name:<57}🔄 {now}\n{'=' * 72}")

    trip_lst = [each[4] for each in rows]                       # Get the list of trips to enquiry RT status
    response = current_trips.enquiry(station_name, trip_lst)
    if not response: print("No real-time data available.")


    for each in rows:
        route_color, platform, headsign, dep_time, trip_id, stop_seq, block_id, direction_id, stop_name = each

        # Showing dest for trip passing city's station if inbound trains heading to Flinders Street first
        next_trip = find_next_trip_in_block(conn, block_id, trip_id)
        if next_trip and direction_id == "1" and any(word in station_name for word in CITY_STATIONS):
            headsign = f"{next_trip[0]}"

        # Default scheduled time calculations
        mins = minutes_until(dep_time)
        dep_time_display = format_time_display(dep_time)

        # Check with realtime response
        delay_int = 0   # Assuming no delay
        trip_relationship = ""
        if response and trip_id in response and response[trip_id]:
            stop_data = response[trip_id][0]  # Only one stop matching station_name
            trip_relationship = response[trip_id][0]["relationship"]
            new_dep_time = stop_data["realtime"]
            delay_int = stop_data["delay"]

            # Calculate mins until new departure
            mins = minutes_until(new_dep_time)
            if dep_time_display == new_dep_time:    dep_time_display = f"{new_dep_time}"
            else:                                   dep_time_display = f"{dep_time_display} → {new_dep_time}"


        # below to be added in JS

        delay_str = ""  # Trips and Delay Status
        if trip_relationship == "CANCELED": mins_display = f"{'CANCELED':>9}"
        elif mins < 0:                      mins_display = f"{'DEPARTED':>9}"
        elif mins == 0:                     mins_display = f"{'DEPARTING':>9}"
        elif mins == 1:                     mins_display = f"{'ARRIVING':>9}"
        else:
            mins_display = f"{mins:>5} min"
            if delay_int > 0:   delay_str = f"{colour_text("FF0000", f"+{delay_int}m")}"
            elif delay_int < 0: delay_str = f"{colour_text("FFFF00", f"{delay_int}m")}"



        print(  f"{colour_text(route_color, "█")} {platform:<3}  "
                f"{headsign:<35}"
                f"{dep_time_display:>15} {mins_display} {delay_str} {trip_id if show_debug else ""} {block_id if show_debug else ""} {direction_id if show_debug else ""}"
        )


        if show_stopping_detail:
            next_stops = get_next_stops(conn, trip_id, stop_seq)
            if next_stops:  render_next_stops(next_stops)
            else:           print("└ Terminates")


def load_timetable():
    print("Loading Timetable...")
    conn = sqlite3.connect(DB_FILE)
    load_table(conn, "stops", "stops.txt")
    load_table(conn, "stop_times", "stop_times.txt")
    load_table(conn, "trips", "trips.txt")
    load_table(conn, "routes", "routes.txt")
    load_table(conn, "calendar", "calendar.txt")
    os.system('cls' if os.name == 'nt' else 'clear')

    return conn

if __name__ == "__main__":

    conn = load_timetable()
    t = input("Station Name: ")
    while t != "":
        os.system('cls' if os.name == 'nt' else 'clear')

        # update current time for enquiry for each loop
        now = datetime.now().strftime("%H:%M:%S")
        five_mins_ago = (datetime.now() - timedelta(minutes=3)).strftime("%H:%M:%S")
        date = datetime.now().strftime("%d/%m/%Y")
        weekday = datetime.now().strftime("%A").lower()
        today = datetime.now().strftime("%Y%m%d")

        main(t, conn)  # pass connection instead of creating inside main
        time.sleep(30)

    conn.close()

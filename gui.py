import csv
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import sqlite3
from gtfs_query import get_station_data
import os

GTFS_PATH = "gtfs_metro_trains/"
DB_FILE = "gtfs.db"

app = FastAPI()

# Serve frontend
app.mount("/frontend", StaticFiles(directory="frontend", html=True), name="frontend")


def load_table(conn, table, filename):
    with open(os.path.join(GTFS_PATH, filename), encoding="utf-8") as f:
        reader = csv.reader(f)
        headers = next(reader)
        conn.execute(f"DROP TABLE IF EXISTS {table}")
        conn.execute(f"CREATE TABLE {table} ({','.join(h + ' TEXT' for h in headers)})")
        for row in reader:
            conn.execute(f"INSERT INTO {table} VALUES ({','.join('?' * len(row))})", row)
    conn.commit()


def init_db():
    if not os.path.exists(DB_FILE):
        conn = sqlite3.connect(DB_FILE)
        load_table(conn, "stops", "stops.txt")
        load_table(conn, "stop_times", "stop_times.txt")
        load_table(conn, "trips", "trips.txt")
        load_table(conn, "routes", "routes.txt")
        load_table(conn, "calendar", "calendar.txt")
        conn.close()


init_db()


# ----------------------------
# API endpoint
# ----------------------------
@app.get("/api/trains")
def trains(station: str):
    conn = sqlite3.connect(DB_FILE)
    data = get_station_data(station, conn)
    conn.close()
    return data

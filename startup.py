import csv
from datetime import datetime, timedelta
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import sqlite3
import current_trips
from gtfs_query import get_station_data
import os
import webbrowser

# Frontend

GTFS_PATH = "gtfs_metro_trains/"
DB_FILE = "gtfs.db"

app = FastAPI()
app.mount("/frontend", StaticFiles(directory="frontend", html=True), name="frontend")

def load_table(conn, table, filename):
    """
    Load a GTFS file into the SQLite database.
    """
    with open(os.path.join(GTFS_PATH, filename), encoding="utf-8") as f:
        reader = csv.reader(f)
        headers = next(reader)
        conn.execute(f"DROP TABLE IF EXISTS {table}")
        conn.execute(f"CREATE TABLE {table} ({','.join(h + ' TEXT' for h in headers)})")
        for row in reader:
            conn.execute(f"INSERT INTO {table} VALUES ({','.join('?' * len(row))})", row)
    conn.commit()

def init_db():
    """
    Initialize the database if it doesn't exist.
    """
    if not os.path.exists(DB_FILE):
        conn = sqlite3.connect(DB_FILE)
        load_table(conn, "stops", "stops.txt")
        load_table(conn, "stop_times", "stop_times.txt")
        load_table(conn, "trips", "trips.txt")
        load_table(conn, "routes", "routes.txt")
        load_table(conn, "calendar", "calendar.txt")
        conn.close()

# ----------------------------
# API endpoint
# ----------------------------
@app.get("/api/trains")
def trains(station: str):
    """
    Get train data for a specific station.
    """
    conn = sqlite3.connect(DB_FILE)
    data = get_station_data(station, conn)
    conn.close()
    return data

@app.get("/api/db-status")
def db_status():
    """
    Check if the database is older than 7 days.
    """
    age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(DB_FILE))
    is_stale = age > timedelta(days=7)
    return {"is_stale": is_stale}

@app.get("/api/key-check")
def api_key_check():
    """
    get backend info for API key status
    """
    key, status = current_trips.load_api_key()
    return {"status": status}

if __name__ == "__main__":
    init_db()
    webbrowser.open("http://127.0.0.1:8000/frontend/index.html", new=2)
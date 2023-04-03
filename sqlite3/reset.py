import sys
import sqlite3
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

con = sqlite3.connect("foxtons.db")
cur = con.cursor()

action = sys.argv[1]

if action == "properties":
    cur.execute("DROP TABLE IF EXISTS properties")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS properties(
            address TEXT, 
            url TEXT,
            id TEXT PRIMARY KEY
        )
    """)
elif action == "timeline":
    cur.execute("DROP TABLE IF EXISTS timeline")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS timeline(
            price_pcm REAL,
            id TEXT,
            is_reduced BOOLEAN,
            scrape_date TEXT,
            scrape_epoch REAL,
            PRIMARY KEY (id, scrape_date)
        )
    """)



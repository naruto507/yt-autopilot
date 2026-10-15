import os, sqlite3, datetime as dt
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
load_dotenv()
TZ = ZoneInfo(os.getenv("TIMEZONE", "UTC"))

def q(sql, args=(), one=False):
    c = sqlite3.connect("data.db"); c.row_factory = sqlite3.Row
    rows = c.execute(sql, args).fetchall(); c.commit(); c.close()
    return (rows[0] if rows else None) if one else rows

def init():
    q("""CREATE TABLE IF NOT EXISTS channels(id TEXT PRIMARY KEY, title TEXT, niche TEXT DEFAULT '',
       style TEXT DEFAULT '', fmt TEXT DEFAULT 'shorts', voice TEXT DEFAULT 'en-US-AndrewNeural',
       times TEXT DEFAULT '09:00,18:00', buffer INTEGER DEFAULT 3, auto INTEGER DEFAULT 0)""")
    q("""CREATE TABLE IF NOT EXISTS jobs(id INTEGER PRIMARY KEY AUTOINCREMENT, channel TEXT, topic TEXT,
       status TEXT DEFAULT 'queued', title TEXT, publish_at TEXT, yt_id TEXT, err TEXT,
       created TEXT DEFAULT CURRENT_TIMESTAMP)""")
    q("UPDATE jobs SET status='queued' WHERE status='making'")

def next_slot(ch):
    """Next free posting time (UTC ISO) from the channel's daily times."""
    used = {r["publish_at"] for r in q("SELECT publish_at FROM jobs WHERE channel=? AND status!='failed'", (ch["id"],))}
    now = dt.datetime.now(TZ) + dt.timedelta(minutes=20)
    for d in range(60):
        day = (now + dt.timedelta(days=d)).date()
        for t in sorted(x.strip() for x in ch["times"].split(",")):
            h, m = map(int, t.split(":"))
            s = dt.datetime(day.year, day.month, day.day, h, m, tzinfo=TZ)
            iso = s.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
            if s > now and iso not in used:
                return iso

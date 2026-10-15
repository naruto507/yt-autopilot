import hmac, os, sys, threading, time, datetime as dt
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"; os.environ["OAUTHLIB_RELAX_TOKEN_SCOPE"] = "1"
from flask import Flask, redirect, render_template_string, request, session
from core import q, init, next_slot
import brain, media, yt

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY") or os.urandom(24)
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax",
                  SESSION_COOKIE_SECURE=yt.BASE.startswith("https"), PERMANENT_SESSION_LIFETIME=60 * 60 * 24 * 30)
PW = os.getenv("DASH_PASSWORD", "")
LOGIN = '<!doctype html><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1"><body style="font:16px system-ui;max-width:340px;margin:20vh auto;padding:0 12px"><h2>YouTube Autopilot</h2><form method=post><input type=password name=pw placeholder=Password autofocus style="width:100%;padding:10px;box-sizing:border-box"><button style="width:100%;padding:10px;margin-top:8px">Login</button></form>{{m}}'

@app.before_request
def guard():
    if PW and request.endpoint != "login" and not session.get("ok"):
        return redirect("/login")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if PW and hmac.compare_digest(request.form.get("pw", ""), PW):
            session.permanent = True; session["ok"] = True
            return redirect("/")
        time.sleep(1.5)  # slow down password guessing
        return render_template_string(LOGIN, m="Wrong password"), 401
    return render_template_string(LOGIN, m="")
PAGE = """<!doctype html><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1"><meta http-equiv=refresh content=60><title>YouTube Autopilot</title>
<style>body{font:15px system-ui;max-width:1000px;margin:24px auto;padding:0 12px}input,select{margin:2px}
form{border:1px solid #ccc;padding:10px;margin:10px 0;border-radius:8px}.w{overflow-x:auto}@media(max-width:600px){input:not([type=checkbox]),select,button{width:100%;box-sizing:border-box;padding:9px;margin:3px 0}}td,th{border-bottom:1px solid #ddd;padding:4px 8px;text-align:left}</style>
<h1>YouTube Autopilot</h1><a href=/connect><button>➕ YouTube চ্যানেল যোগ করুন</button></a>
{% for c in chs %}<form method=post action=/channel/{{c.id}}><b>{{c.title}}</b><br>
niche <input name=niche value="{{c.niche}}" size=22> style/ভাষা <input name=style value="{{c.style}}" size=30>
format <select name=fmt><option {{'selected' if c.fmt=='shorts'}}>shorts<option {{'selected' if c.fmt=='long'}}>long</select>
voice <input name=voice value="{{c.voice}}" size=20><br>
posting times <input name=times value="{{c.times}}" size=14> buffer <input name=buffer type=number value="{{c.buffer}}" style="width:50px">
<label><input type=checkbox name=auto {{'checked' if c.auto}}> 🤖 Autopilot (নিজে topic বেছে video বানাবে)</label> <button>Save</button></form>
<form method=post action=/make/{{c.id}}><input name=topic size=50 placeholder="topic (খালি রাখলে AI বেছে নেবে)"><button>🎬 এখনই video বানাও</button></form>{% endfor %}
<h3>Jobs</h3><div class=w><table><tr><th>#<th>status<th>title / topic<th>publish (UTC)<th>video<th>error<th></tr>
{% for j in jobs %}<tr><td>{{j.id}}<td>{{j.status}}<td>{{j.title or j.topic or '(AI picks)'}}<td>{{j.publish_at}}
<td>{% if j.yt_id %}<a href="https://studio.youtube.com/video/{{j.yt_id}}/edit" target=_blank>Studio</a>{% endif %}
<td>{{j.err or ''}}<td>{% if j.status=='failed' %}<form method=post action=/retry/{{j.id}} style="border:0;padding:0;margin:0"><button>retry</button></form>{% endif %}</tr>{% endfor %}</table></div>"""

@app.route("/")
def home():
    return render_template_string(PAGE, chs=q("SELECT * FROM channels"), jobs=q("SELECT * FROM jobs ORDER BY id DESC LIMIT 40"))

@app.route("/connect")
def connect(): return redirect(yt.start())

@app.route("/oauth")
def oauth():
    if "error" in request.args: return request.args["error"], 400
    cid, title = yt.finish(request.args["state"], yt.BASE + request.full_path)
    q("INSERT OR IGNORE INTO channels(id,title) VALUES(?,?)", (cid, title))
    return redirect("/")

@app.post("/channel/<cid>")
def save(cid):
    f = request.form
    q("UPDATE channels SET niche=?,style=?,fmt=?,voice=?,times=?,buffer=?,auto=? WHERE id=?",
      (f["niche"], f["style"], f["fmt"], f["voice"], f["times"], int(f["buffer"] or 3), 1 if "auto" in f else 0, cid))
    return redirect("/")

def add_job(ch, topic):
    slot = next_slot(ch)
    if slot: q("INSERT INTO jobs(channel,topic,publish_at) VALUES(?,?,?)", (ch["id"], topic or None, slot))

@app.post("/make/<cid>")
def make(cid):
    add_job(q("SELECT * FROM channels WHERE id=?", (cid,), one=True), request.form.get("topic", "").strip())
    return redirect("/")

@app.post("/retry/<int:jid>")
def retry(jid):
    j = q("SELECT * FROM jobs WHERE id=?", (jid,), one=True)
    ch = q("SELECT * FROM channels WHERE id=?", (j["channel"],), one=True)
    q("UPDATE jobs SET status='queued',err=NULL,publish_at=? WHERE id=?", (next_slot(ch), jid))
    return redirect("/")

def run(job):
    ch = q("SELECT * FROM channels WHERE id=?", (job["channel"],), one=True)
    try:
        q("UPDATE jobs SET status='making' WHERE id=?", (job["id"],))
        past = [r["title"] or r["topic"] or "" for r in q("SELECT title,topic FROM jobs WHERE channel=?", (ch["id"],))]
        try: ideas = yt.trending(ch["id"], ch["niche"])
        except Exception: ideas = []
        topic = job["topic"] or brain.pick_topic(ch, ideas, past)
        pkg = brain.make_package(ch, topic, ideas)
        work = f"work/{job['id']}"; os.makedirs(work, exist_ok=True)
        mp4, th = media.build(ch, pkg, work)
        vid = yt.upload(ch["id"], mp4, th, pkg, job["publish_at"], ch["fmt"] == "long")
        q("UPDATE jobs SET status='scheduled',title=?,topic=?,yt_id=? WHERE id=?", (pkg["title"], topic, vid, job["id"]))
    except Exception as e:
        q("UPDATE jobs SET status='failed',err=? WHERE id=?", (str(e)[:500], job["id"]))

def fill():
    """Autopilot: keep `buffer` videos queued/scheduled ahead. Pauses an hour after any failure."""
    now = dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.000Z")
    for ch in q("SELECT * FROM channels WHERE auto=1"):
        if q("SELECT 1 FROM jobs WHERE channel=? AND status='failed' AND created>datetime('now','-1 hour')", (ch["id"],), one=True):
            continue
        n = q("SELECT COUNT(*) c FROM jobs WHERE channel=? AND (status IN ('queued','making') OR (status='scheduled' AND publish_at>?))",
              (ch["id"], now), one=True)["c"]
        if n < ch["buffer"]: add_job(ch, None)

def worker():
    while True:
        try:
            fill()
            j = q("SELECT * FROM jobs WHERE status='queued' ORDER BY id LIMIT 1", one=True)
            if j: run(j); continue
        except Exception as e: print("worker:", e)
        time.sleep(30)

if __name__ == "__main__":
    host = os.getenv("HOST", "127.0.0.1")
    if host != "127.0.0.1" and not PW:
        sys.exit("DASH_PASSWORD is required when HOST is not 127.0.0.1")
    init()
    threading.Thread(target=worker, daemon=True).start()
    app.run(host=host, port=5000)

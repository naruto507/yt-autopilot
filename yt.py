import os, datetime as dt
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
SCOPES = ["https://www.googleapis.com/auth/youtube.upload", "https://www.googleapis.com/auth/youtube.readonly"]
BASE = os.getenv("BASE_URL", "http://localhost:5000")
_flows = {}

def start():
    f = Flow.from_client_secrets_file("client_secret.json", SCOPES, redirect_uri=BASE + "/oauth")
    url, state = f.authorization_url(access_type="offline", prompt="consent")
    _flows[state] = f
    return url

def finish(state, response_url):
    f = _flows.pop(state); f.fetch_token(authorization_response=response_url); c = f.credentials
    ch = build("youtube", "v3", credentials=c).channels().list(part="snippet", mine=True).execute()["items"][0]
    os.makedirs("tokens", exist_ok=True)
    open(f"tokens/{ch['id']}.json", "w").write(c.to_json())
    return ch["id"], ch["snippet"]["title"]

def service(cid):
    p = f"tokens/{cid}.json"; c = Credentials.from_authorized_user_file(p, SCOPES)
    if not c.valid:
        c.refresh(Request()); open(p, "w").write(c.to_json())
    return build("youtube", "v3", credentials=c)

def trending(cid, niche, days=30):
    """Real top videos in the niche from the last N days (costs ~100 quota units)."""
    y = service(cid); after = (dt.datetime.utcnow() - dt.timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")
    ids = [i["id"]["videoId"] for i in y.search().list(part="id", q=niche, type="video", order="viewCount",
           publishedAfter=after, maxResults=15).execute()["items"]]
    v = y.videos().list(part="snippet,statistics", id=",".join(ids)).execute()["items"]
    v.sort(key=lambda x: -int(x["statistics"].get("viewCount", 0)))
    return [f'{x["snippet"]["title"]} ({x["statistics"].get("viewCount", 0)} views)' for x in v[:10]]

def upload(cid, path, thumb, pkg, publish_at, long):
    y = service(cid)
    body = {"snippet": {"title": pkg["title"], "description": pkg["description"], "tags": pkg["tags"][:15], "categoryId": "22"},
            "status": {"privacyStatus": "private" if publish_at else "public", "selfDeclaredMadeForKids": False,
                       "containsSyntheticMedia": True}}
    if publish_at: body["status"]["publishAt"] = publish_at
    r = y.videos().insert(part="snippet,status", body=body,
                          media_body=MediaFileUpload(path, chunksize=-1, resumable=True)).execute()
    if long:
        try: y.thumbnails().set(videoId=r["id"], media_body=MediaFileUpload(thumb)).execute()
        except Exception: pass
    return r["id"]

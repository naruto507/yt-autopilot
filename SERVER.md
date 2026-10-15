# সার্ভারে চালানো (Ubuntu 22.04/24.04, ≥2 GB RAM) ও ফোন থেকে কন্ট্রোল

## ১. কম্পিউটারে আগে চ্যানেল যোগ করুন
প্রথমে নিজের কম্পিউটারে `python app.py` চালিয়ে `localhost:5000` থেকে চ্যানেল যোগ করুন
(এতে `tokens/` ফোল্ডার ও `data.db` তৈরি হয়)।

## ২. সার্ভার প্রস্তুত
```
sudo apt update && sudo apt install -y python3-venv ffmpeg fonts-dejavu-core caddy
sudo useradd -m -s /bin/bash ytbot
sudo mkdir /opt/yt-autopilot && sudo chown ytbot: /opt/yt-autopilot
```
(`caddy` না পেলে caddyserver.com/docs/install দেখুন।)

## ৩. ফাইল কপি (কম্পিউটার থেকে)
```
scp -r yt-autopilot/* .env client_secret.json tokens data.db ytbot@SERVER_IP:/opt/yt-autopilot/
```
`tokens/` এ আপনার YouTube লগইন আছে, কাউকে দেবেন না। সার্ভারে `chmod 600 tokens/* .env`।

## ৪. সার্ভারে সেটআপ
```
cd /opt/yt-autopilot
python3 -m venv venv && venv/bin/pip install -r requirements.txt
cp /usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf font.ttf
```
`.env` এ বদলান:
```
HOST=127.0.0.1
DASH_PASSWORD=একটা-লম্বা-শক্ত-পাসওয়ার্ড
SECRET_KEY=যেকোনো-লম্বা-র‍্যান্ডম-লেখা
BASE_URL=https://yourdomain.com
```
Google Cloud এর OAuth client এ Redirect URI হিসেবে `https://yourdomain.com/oauth` ও যোগ করুন (নতুন চ্যানেল যোগ করতে লাগবে)।

## ৫. চালু করুন
```
sudo cp deploy/ytautopilot.service /etc/systemd/system/
sudo systemctl enable --now ytautopilot
sudo cp deploy/Caddyfile /etc/caddy/Caddyfile   # আগে yourdomain.com বদলান
sudo systemctl restart caddy
journalctl -u ytautopilot -f      # লগ দেখতে
```
ফোনের ব্রাউজারে `https://yourdomain.com` খুলে পাসওয়ার্ড দিন। হোম স্ক্রিনে শর্টকাট রাখা যায়।

নোট: `HOST=127.0.0.1` রাখলে অ্যাপ শুধু Caddy-র (HTTPS) মাধ্যমে খোলা থাকে, সরাসরি ইন্টারনেটে নয়।
বাংলা ক্যাপশনের জন্য বাংলা ফন্ট (`fc-list :lang=bn` দেখুন) ও ফন্টের জটিল অক্ষর জোড়া লাগানোর সাপোর্ট লাগে; সার্ভারে আগে একটা ছোট ভিডিও বানিয়ে দেখে নিন।

# YouTube Autopilot

আইডিয়া → হুক (স্কোর করা) → স্ক্রিপ্ট → ভয়েস → ফুটেজ → এডিট + ক্যাপশন → থিম্বনেইল → টাইটেল/ডেসক্রিপশন/ট্যাগ → নির্দিষ্ট সময়ে YouTube-এ আপলোড।
Dashboard থেকে একাধিক YouTube চ্যানেল যোগ করা যায়। Autopilot চালু থাকলে নিজেই topic বেছে নেয়।

## Setup (একবার)
1. Python 3.10+ ও **FFmpeg** ইনস্টল করুন (`ffmpeg -version` চলতে হবে)।
2. `pip install -r requirements.txt`
3. যেকোনো `.ttf` ফন্ট প্রজেক্ট ফোল্ডারে `font.ttf` নামে রাখুন (ক্যাপশন ও থিম্বনেইলের জন্য; বাংলা লিখলে বাংলা ফন্ট দিন)।
4. `.env.example` কপি করে `.env` বানান: Anthropic API key, Pexels free key (stock footage), TIMEZONE (যেমন `Asia/Dhaka`)।
5. Google Cloud Console: নতুন project → **YouTube Data API v3** enable → OAuth consent screen
   (নিজের email Test user দিন, পরে **"In production"** এ পাঠান, নইলে token ৭ দিনে expire হয়) →
   Credentials → OAuth client ID → **Web application** → Redirect URI: `http://localhost:5000/oauth` →
   JSON নামিয়ে `client_secret.json` নামে ফোল্ডারে রাখুন।
6. `python app.py` → ব্রাউজারে `http://localhost:5000` → **➕ YouTube চ্যানেল যোগ করুন**।

## ব্যবহার
- চ্যানেল যোগ করার পর niche, style/ভাষা, format (shorts/long), voice, posting times, buffer সেট করে Save করুন।
- **🎬 এখনই video বানাও**: topic দিন বা খালি রাখুন। ভিডিও বানিয়ে YouTube-এ private আপলোড হবে এবং পরের খালি slot-এ নিজে public হবে (`publishAt`)।
- **Autopilot** চালু করলে buffer সংখ্যক ভিডিও সবসময় আগে থেকে তৈরি থাকবে। কোনো ভিডিও fail করলে ওই চ্যানেলের autopilot এক ঘণ্টা থামে (খরচ বাঁচাতে)।
- বাংলা ভিডিও: style-এ "Write in Bengali" দিন, voice দিন `bn-BD-NabanitaNeural` বা `bn-BD-PradeepNeural`।
  (`hookscore` ইংরেজি শব্দের উপর বানানো, বাংলা হুকে স্কোর অর্থহীন।)

## Viral-এর জন্য যা আছে (গ্যারান্টি নয়)
- আপনার niche-এ গত ৩০ দিনে সবচেয়ে বেশি view পাওয়া ভিডিওর টাইটেল YouTube API থেকে এনে প্যাটার্ন শেখানো হয় (কপি নয়)।
- ৫টা হুক লিখে ২১ ফর্মুলার উপর স্কোর করে সেরাটা নেওয়া হয়; দুর্বল হলে একবার আবার লেখে ([youtube-agent-skill](https://github.com/Jakeschincariol/youtube-agent-skill), MIT)।
- টাইটেল ≤ ৬০ অক্ষর, আলাদা অ্যাঙ্গেলের থিম্বনেইল টেক্সট, শর্টসে লুপ-এন্ডিং, প্রতি সিনে নতুন ভিজ্যুয়াল।
- **কোনো টুলই million view নিশ্চিত করতে পারে না।** সেটা niche, কনটেন্টের মান, ধারাবাহিকতা আর ভাগ্যের উপর নির্ভর করে।

## সীমাবদ্ধতা (আগে জেনে নিন)
- **নতুন API project-এর আপলোড private-এ আটকে থাকে** যতক্ষণ না Google-এর API compliance audit পাশ হয়। প্রথমে নিজে Studio-তে দেখে নিন।
- Quota: একটা আপলোড ≈ ১৬০০ unit, দৈনিক ডিফল্ট ১০,০০০ ⇒ দিনে প্রায় ৬টা ভিডিও।
- আপলোডে `containsSyntheticMedia` চালু আছে (AI ভয়েস ডিসক্লোজার)। YouTube-এর "inauthentic/repetitive content" নীতিতে কম-প্রচেষ্টার ব্যাপক কনটেন্ট মনিটাইজেশন হারাতে পারে। নিয়মিত নিজে ভিডিও দেখে নিন।
- `edge-tts` Microsoft Edge-এর অনানুষ্ঠানিক ভয়েস সার্ভিস ব্যবহার করে। ব্যবসায়িকভাবে চালালে `media.tts()` বদলে ElevenLabs/Google TTS দিন।
- ফ্যাক্ট নিজে যাচাই করুন: AI ভুল তথ্য লিখতে পারে। Health/money niche এ বিশেষ সতর্ক থাকুন।
- কম্পিউটার চালু না থাকলে নতুন ভিডিও বানানো বন্ধ থাকে; তবে আগে আপলোড হয়ে যাওয়া ভিডিও YouTube নিজেই সময়মতো public করবে।

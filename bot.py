import os, json, requests, subprocess, random
from io import BytesIO

BOT_TOKEN = os.environ['BOT_TOKEN']
CHANNEL_ID = os.environ['CHANNEL_ID']
QUEUE_FILE = "queue.json"          # remaining indices সংরক্ষণের জন্য

# ---------- পোস্ট লোড ----------
with open('posts.json', 'r', encoding='utf-8') as f:
    posts = json.load(f)

total = len(posts)
print(f"📊 Total posts: {total}")
if total == 0:
    print("❌ No posts!")
    exit(1)

# ---------- বাকি পোস্টের তালিকা (random non‑repeating) ----------
try:
    with open(QUEUE_FILE, 'r') as f:
        remaining = json.load(f)
    print(f"📂 Queue loaded: {len(remaining)} posts left")
except:
    # প্রথমবার – সব ইন্ডেক্স শাফল করে নেই
    remaining = list(range(total))
    random.shuffle(remaining)
    print(f"📂 No queue file. Created shuffled queue ({len(remaining)} indices)")

# queue খালি হলে আবার সব ইন্ডেক্স শাফল করি
if not remaining:
    remaining = list(range(total))
    random.shuffle(remaining)
    print("🔄 Queue empty – reshuffled all indices")

# সবচেয়ে শেষের ইন্ডেক্স নিই (যেকোনো পজিশন থেকে নেওয়া যায়)
current_index = remaining.pop()

# পোস্ট বের করা
post = posts[current_index]
text = post['text']
print(f"📝 Post index: {current_index}, preview: {text[:60]}...")

# ---------- টেলিগ্রামে পাঠানো (শুধু টেক্সট) ----------
reply_markup = {
    "inline_keyboard": [
        [{"text": "🔗 Join Our List", "url": "https://t.me/addlist/57pQLQQl0Oo1MDk9"}]
    ]
}

def send_telegram_text(text):
    """লম্বা টেক্সট ভাগ করে পাঠানোর ফাংশন"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    max_msg_len = 4000
    parts = [text[i:i+max_msg_len] for i in range(0, len(text), max_msg_len)]
    for idx, part in enumerate(parts):
        payload = {
            "chat_id": CHANNEL_ID,
            "text": part,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
            "reply_markup": reply_markup if idx == 0 else None  # বাটন শুধু প্রথম মেসেজে
        }
        resp = requests.post(url, json=payload, timeout=15).json()
        if not resp.get('ok'):
            print(f"❌ Text send error: {resp}")
        else:
            print(f"✅ Part {idx+1}/{len(parts)} sent")

# পাঠান
send_telegram_text(text)

# ---------- queue সংরক্ষণ ----------
with open(QUEUE_FILE, 'w') as f:
    json.dump(remaining, f)
print(f"💾 Queue updated: {len(remaining)} posts left")

# ---------- গিট কমিট ও পুশ (queue.json আপডেট রাখতে) ----------
try:
    subprocess.run(["git", "config", "user.name", "GitHub Actions"], check=True)
    subprocess.run(["git", "config", "user.email", "actions@github.com"], check=True)
    subprocess.run(["git", "add", QUEUE_FILE], check=True)
    diff = subprocess.run(["git", "diff", "--cached", "--quiet"], capture_output=True)
    if diff.returncode != 0:
        subprocess.run(["git", "commit", "-m", "Update post queue"], check=True)
        subprocess.run(["git", "pull", "--rebase", "origin", "main"], check=True)
        subprocess.run(["git", "push", "origin", "main"], check=True)
        print("✅ Queue committed and pushed")
    else:
        print("ℹ️  No change in queue")
except subprocess.CalledProcessError as e:
    print(f"⚠️ Git error (push may have failed): {e}")

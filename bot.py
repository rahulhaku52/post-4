import os, json, requests, subprocess, random

BOT_TOKEN = os.environ['BOT_TOKEN']
CHANNEL_IDS = [cid.strip() for cid in os.environ['CHANNEL_IDS'].split(',') if cid.strip()]

print(f"📡 Channels: {CHANNEL_IDS}")

# ---------- পোস্ট লোড ----------
with open('posts.json', 'r', encoding='utf-8') as f:
    posts = json.load(f)

total = len(posts)
print(f"📊 Total posts: {total}")
if total == 0:
    print("❌ No posts!")
    exit(1)

# ---------- ইনলাইন বাটন ----------
reply_markup = {
    "inline_keyboard": [
        [{"text": "🔗 Join Our List", "url": "https://t.me/addlist/AceR51Tr9VE3Njk1"}]
    ]
}

def send_text(channel_id, text):
    """একটি চ্যানেলে সম্পূর্ণ টেক্সট পাঠাবে (ভাগ করে যদি বড় হয়)"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    max_len = 4000
    parts = [text[i:i+max_len] for i in range(0, len(text), max_len)]
    for idx, part in enumerate(parts):
        payload = {
            "chat_id": channel_id,
            "text": part,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
            "reply_markup": reply_markup if idx == 0 else None
        }
        resp = requests.post(url, json=payload, timeout=15).json()
        if not resp.get('ok'):
            print(f"❌ [{channel_id}] Part {idx+1} error: {resp}")
            return False
    print(f"✅ [{channel_id}] Message sent")
    return True

# ---------- প্রতিটি চ্যানেলের জন্য কাজ ----------
for cid in CHANNEL_IDS:
    # queue ফাইলের নাম তৈরি (নিউমেরিক আইডির জন্যও সুন্দর নাম)
    safe_name = cid.lstrip('@').replace('-', '_')
    queue_file = f"queue_{safe_name}.json"

    # queue লোড অথবা নতুন শাফল করা queue তৈরি
    try:
        with open(queue_file, 'r') as f:
            remaining = json.load(f)
        print(f"📂 [{cid}] Queue loaded: {len(remaining)} posts left")
    except:
        remaining = list(range(total))
        random.shuffle(remaining)
        print(f"📂 [{cid}] No queue file → created shuffled queue")

    # queue খালি হলে আবার পুরো সেট শাফল
    if not remaining:
        remaining = list(range(total))
        random.shuffle(remaining)
        print(f"🔄 [{cid}] Queue empty → reshuffled")

    # পরবর্তী পোস্টের ইনডেক্স বের করা
    post_index = remaining.pop()
    post_text = posts[post_index]['text']
    print(f"📤 [{cid}] Sending post index {post_index}: {post_text[:60]}...")

    # পাঠানো
    if send_text(cid, post_text):
        # সফল হলে queue আপডেট
        with open(queue_file, 'w') as f:
            json.dump(remaining, f)

# ---------- গিটে queue ফাইলগুলো আপডেট ----------
try:
    subprocess.run(["git", "config", "user.name", "GitHub Actions"], check=True)
    subprocess.run(["git", "config", "user.email", "actions@github.com"], check=True)
    subprocess.run(["git", "add", "queue_*.json"], check=True)
    diff = subprocess.run(["git", "diff", "--cached", "--quiet"], capture_output=True)
    if diff.returncode != 0:
        subprocess.run(["git", "commit", "-m", "Update channel queues"], check=True)
        subprocess.run(["git", "pull", "--rebase", "origin", "main"], check=True)
        subprocess.run(["git", "push", "origin", "main"], check=True)
        print("✅ Queues committed and pushed")
    else:
        print("ℹ️  No changes in queues")
except subprocess.CalledProcessError as e:
    print(f"⚠️ Git error (push may have failed): {e}")

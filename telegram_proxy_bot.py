# proxy_collector.py
import os, requests, re

BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID")

SOURCES = [
    "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/sub/sub_merge.txt",
    "https://raw.githubusercontent.com/peasoft/NoMoreWalls/master/list.txt",
]

def fetch_proxies():
    proxies = []
    for url in SOURCES:
        try:
            r = requests.get(url, timeout=10)
            for line in r.text.splitlines():
                line = line.strip()
                if line and (line.startswith("vmess://") or line.startswith("vless://") or line.startswith("trojan://")):
                    proxies.append(line)
        except Exception as e:
            print(f"Error fetching from {url}: {e}")
    return list(dict.fromkeys(proxies))  # حذف تکراری

def save_proxies(proxies):
    try:
        with open("sub.txt", "w", encoding="utf-8") as f:
            f.write("\n".join(proxies))
    except Exception as e:
        print("Error saving proxies:", e)

def send_telegram(proxies):
    if not BOT_TOKEN or not CHAT_ID:
        print("BOT_TOKEN یا CHAT_ID تنظیم نشده.")
        return
    text = "\n".join(proxies)
    chunk_size = 2000  # تقسیم متن طولانی
    for i in range(0, len(text), chunk_size):
        chunk = text[i:i+chunk_size]
        try:
            requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",

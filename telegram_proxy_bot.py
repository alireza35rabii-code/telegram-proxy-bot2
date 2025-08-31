# proxy_collector.py
import os, requests, re

BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID")

# منابع پروکسی (می‌تونی بعداً اضافه کنی)
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
        except:
            pass
    return list(dict.fromkeys(proxies))  # حذف تکراری

def save_proxies(proxies):
    with open("sub.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(proxies))

def send_telegram(proxies):
    if not BOT_TOKEN or not CHAT_ID:
        print("BOT_TOKEN یا CHAT_ID تنظیم نشده.")
        return
    text = "\n".join(proxies)
    # تلگرام محدودیت 4096 کاراکتر داره، بنابراین اگه طولانیه تقسیم می‌کنیم
    chunk_size = 2000
    for i in range(0, len(text), chunk_size):
        chunk = text[i:i+chunk_size]
        try:
            requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                          data={"chat_id": CHAT_ID, "text": chunk})
        except:
            continue

def main():
    proxies = fetch_proxies()
    if proxies:
        save_proxies(proxies)
        send_telegram(proxies)
        print(f"Found {len(proxies)} proxies and sent to Telegram.")
    else:
        print("No proxies found.")

if __name__ == "__main__":
    main()

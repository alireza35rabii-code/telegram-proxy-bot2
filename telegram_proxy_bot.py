# telegram_proxy_bot.py
import os, re, requests, concurrent.futures, time

BOT_TOKEN = os.getenv("BOT_TOKEN")      # از Secrets خوانده می‌شود
CHAT_ID   = os.getenv("CHAT_ID")        # از Secrets خوانده می‌شود

# منابع پروکسی (می‌تونی بعداً این لیست را بیشتر کنی)
SOURCES = [
    "https://raw.githubusercontent.com/hookzof/socks5_list/master/proxy.txt",
    "https://www.proxy-list.download/api/v1/get?type=socks5",
    "https://www.proxy-list.download/api/v1/get?type=http",
]

# ————— جمع‌آوری پروکسی‌ها —————
def fetch_text(url, timeout=10):
    try:
        r = requests.get(url, timeout=timeout)
        if r.ok:
            return r.text
    except:
        pass
    return ""

def collect_proxies():
    txts = [fetch_text(u) for u in SOURCES]
    combined = "\n".join(txts)
    found = set()
    for ip, port in re.findall(r"(\d+\.\d+\.\d+\.\d+):(\d+)", combined):
        p = int(port)
        if 1 <= p <= 65535:
            found.add(f"{ip}:{p}")
    return list(found)

# ————— تست سریع (ساکس۵/HTTP) —————
def test_proxy(proxy, timeout=6):
    # ابتدا سعی می‌کنیم با socks5 تست کنیم، اگر شکست خورد با http تست می‌کنیم
    proxies_socks = {"http": f"socks5h://{proxy}", "https": f"socks5h://{proxy}"}
    proxies_http  = {"http": f"http://{proxy}",   "https": f"http://{proxy}"}
    test_url = "https://api.telegram.org/botINVALIDTOKEN/getMe"
    try:
        r = requests.get(test_url, proxies=proxies_socks, timeout=timeout)
        # اگر پاسخ از سرور برگشت (خطای auth یا 404) یعنی قابل اتصال است
        if r.status_code < 500:
            return proxy
    except:
        pass
    try:
        r = requests.get(test_url, proxies=proxies_http, timeout=timeout)
        if r.status_code < 500:
            return proxy
    except:
        pass
    return None

# ————— ارسال به تلگرام —————
def send_chunks(lines):
    if not BOT_TOKEN or not CHAT_ID:
        print("BOT_TOKEN یا CHAT_ID تنظیم نشده‌اند.")
        return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    chunk = []
    for p in lines:
        chunk.append(p)
        if len(chunk) >= 40:
            requests.post(url, data={"chat_id": CHAT_ID, "text": "\n".join(chunk)})
            time.sleep(0.8)
            chunk = []
    if chunk:
        requests.post(url, data={"chat_id": CHAT_ID, "text": "\n".join(chunk)})

def main():
    print("Collecting proxies...")
    candidates = collect_proxies()
    print("Found candidates:", len(candidates))
    if not candidates:
        if BOT_TOKEN and CHAT_ID:
            requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                          data={"chat_id": CHAT_ID, "text": "❌ هیچ پروکسی‌ای پیدا نشد."})
        return

    alive = []
    print("Testing proxies (parallel)...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=100) as ex:
        for proxy, ok in zip(candidates, ex.map(test_proxy, candidates)):
            if ok:
                alive.append(proxy)
    alive = list(dict.fromkeys(alive))  # حذف تکراری حفظ ترتیب
    print("Alive count:", len(alive))

    if alive:
        # ذخیره محلی (artifact)
        with open("working.txt", "w") as f:
            for p in alive:
                f.write(p + "\n")
        # ارسال به تلگرام به صورت چند پارتی
        send_chunks(alive)
    else:
        if BOT_TOKEN and CHAT_ID:
            requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                          data={"chat_id": CHAT_ID, "text": "❌ پروکسی سالم پیدا نشد."})

if __name__ == "__main__":
    main()

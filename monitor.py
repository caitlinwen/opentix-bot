import os
import time
import requests
import re
import json

# 監控場次 ID（台北、高雄、屏東）
EVENTS = {
    "2076925048527581185": "台北·國家音樂廳",
    "2079132570898259969": "高雄·衛武營國家藝術文化中心",
    "2072537230141886465": "屏東·演藝廳"
}

LINE_CHANNEL_ACCESS_TOKEN = (os.getenv("LINE_CHANNEL_ACCESS_TOKEN") or "").strip()
LINE_USER_ID = (os.getenv("LINE_USER_ID") or "").strip()

def send_line_message(text_content):
    if not LINE_CHANNEL_ACCESS_TOKEN or not LINE_USER_ID:
        print("Missing LINE credentials.", flush=True)
        return

    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"
    }
    payload = {
        "to": LINE_USER_ID,
        "messages": [{"type": "text", "text": text_content}]
    }
    try:
        res = requests.post(url, json=payload, headers=headers, timeout=10)
        print(f"LINE push status: {res.status_code}", flush=True)
        if res.status_code != 200:
            print(f"LINE error response: {res.text}", flush=True)
    except Exception as e:
        print(f"Failed to push LINE message: {e}", flush=True)

def format_alert(title, venue, event_id, details=""):
    return (
        f"🎹 阿格麗希釋票速報！\n\n"
        f"{title}\n"
        f"📍{venue}\n\n"
        f"{details}\n"
        f"快去 OPENTIX 搶票：\n"
        f"https://www.opentix.life/event/{event_id}"
    )

def check_event(event_id, venue_name):
    page_url = f"https://www.opentix.life/event/{event_id}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
    }
    
    try:
        res = requests.get(page_url, headers=headers, timeout=12)
        if res.status_code != 200:
            print(f"[{venue_name}] HTTP {res.status_code}", flush=True)
            return

        html = res.text

        # 擷取頁面標題
        title_match = re.search(r'<title>(.*?)</title>', html)
        title = title_match.group(1).split('|')[0].strip() if title_match else "瑪莎·阿格麗希音樂會"

        # 1. 檢測結構化 Schema 是否標記 InStock
        is_instock = bool(re.search(r'"availability"\s*:\s*"(?:https?://schema\.org/)?InStock"', html))

        # 2. 檢測 Nuxt 狀態中的售票資訊
        has_remaining_tickets = False
        remaining_matches = re.findall(r'remainingTickets["\']?\s*:\s*(\d+)', html)
        if remaining_matches:
            for count in remaining_matches:
                if int(count) > 0:
                    has_remaining_tickets = True
                    break

        print(f"Checked [{venue_name}] - InStock: {is_instock}, TicketCountFound: {has_remaining_tickets}", flush=True)

        # 釋票觸發條件
        if is_instock or has_remaining_tickets:
            print(f"🚨 [{venue_name}] 偵測到釋票！正在發送 LINE 通知...", flush=True)
            detail_msg = "🎟️ 系統偵測到有座位釋出 (InStock)"
            msg = format_alert(title, venue_name, event_id, detail_msg)
            send_line_message(msg)

    except Exception as e:
        print(f"Error checking {venue_name} ({event_id}): {e}", flush=True)

def poll_for_duration(minutes=9, interval=20):
    end_time = time.time() + (minutes * 60)
    print(f"Starting cloud monitoring loop ({interval}s interval for {minutes}m)...", flush=True)
    
    while time.time() < end_time:
        for eid, vname in EVENTS.items():
            check_event(eid, vname)
        time.sleep(interval)

if __name__ == "__main__":
    loop_mins = int(os.getenv("LOOP_MINUTES", "0"))
    if loop_mins > 0:
        poll_for_duration(minutes=loop_mins, interval=20)
    else:
        for eid, vname in EVENTS.items():
            check_event(eid, vname)

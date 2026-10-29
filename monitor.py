import os
import time
import requests
import re

EVENTS = {
    "2076925048527581185": "台北·國家音樂廳",
    "2079132570898259969": "高雄·衛武營國家藝術文化中心",
    "2072537230141886465": "屏東·演藝廳"
}

LINE_CHANNEL_ACCESS_TOKEN = (os.getenv("LINE_CHANNEL_ACCESS_TOKEN") or "").strip()
LINE_USER_ID = (os.getenv("LINE_USER_ID") or "").strip()

NOTIFIED_EVENTS = set()

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

def format_alert(title, venue, event_id, count_info=""):
    ticket_line = f"🎫 {count_info}\n\n" if count_info else ""
    return (
        f"🎹 阿格麗希釋票速報！\n\n"
        f"{title}\n"
        f"📍{venue}\n\n"
        f"{ticket_line}"
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

        title_match = re.search(r'<title>(.*?)</title>', html)
        title = title_match.group(1).split('|')[0].strip() if title_match else "瑪莎·阿格麗希音樂會"

        # 1. 抓取明確的剩餘票數（例如網頁上的「剩：1」或 JSON 裡的 remainingTickets）
        explicit_rem = re.findall(r'剩\s*[:：]\s*(\d+)', html)
        json_rem = re.findall(r'remainingTickets["\']?\s*:\s*(\d+)', html)
        
        all_counts = [int(c) for c in (explicit_rem + json_rem) if int(c) > 0]
        has_positive_tickets = len(all_counts) > 0
        total_remaining = max(all_counts) if has_positive_tickets else None

        # 2. 備用判定：檢查是否有「電腦配位」或「自行選位」且未被 disabled
        has_buy_button = ("電腦配位" in html or "自行選位" in html) and ("已售完" not in html and "已售罄" not in html)

        is_available = has_positive_tickets or (has_buy_button and '"availability":"InStock"' in html)

        count_desc = f"剩餘票數：約 {total_remaining} 張" if total_remaining else "有票券釋出！"
        print(f"Checked [{venue_name}] - Available: {is_available} (Counts: {all_counts})", flush=True)

        if is_available:
            if event_id not in NOTIFIED_EVENTS:
                print(f"🚨 [{venue_name}] 偵測到釋票！發送 LINE 通知...", flush=True)
                msg = format_alert(title, venue_name, event_id, count_desc)
                send_line_message(msg)
                NOTIFIED_EVENTS.add(event_id)
            else:
                print(f"[{venue_name}] 仍有票，已推播過跳過。", flush=True)
        else:
            if event_id in NOTIFIED_EVENTS:
                print(f"[{venue_name}] 票券已搶完，重置狀態。", flush=True)
                NOTIFIED_EVENTS.remove(event_id)

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

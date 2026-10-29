import os
import time
import requests
import json

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

def check_event(event_id, venue_name):
    # 直接打 OPENTIX 官方內部資料 API，反應最快、資料最精準
    api_url = f"https://www.opentix.life/oapi/v1/events/{event_id}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
    }
    
    try:
        res = requests.get(api_url, headers=headers, timeout=10)
        if res.status_code != 200:
            print(f"[{venue_name}] API HTTP {res.status_code}", flush=True)
            return

        data = res.json()
        title = data.get("title") or "阿格麗希音樂會"
        
        # 統計所有場次的剩餘票數
        total_remaining = 0
        available_prices = set()

        for perf in data.get("performances", []):
            # 統計場次剩餘總票數
            perf_tickets = perf.get("remainingTickets", 0)
            if isinstance(perf_tickets, int) and perf_tickets > 0:
                total_remaining += perf_tickets
            
            # 檢查各個票價階層
            for price_tier in perf.get("prices", []):
                price_val = price_tier.get("price")
                remaining = price_tier.get("remainingTickets", 0)
                # 若該價位有票，記錄該價位
                if remaining > 0 and price_val:
                    available_prices.add(f"NT$ {price_val}")

        has_tickets = total_remaining > 0
        print(f"Checked [{venue_name}] - TicketsFound: {has_tickets} (Remaining: {total_remaining})", flush=True)

        if has_tickets:
            if event_id not in NOTIFIED_EVENTS:
                print(f"🚨 [{venue_name}] 偵測到釋票！發送 LINE 通知...", flush=True)
                
                price_text = f"💰 可購票價：{', '.join(sorted(available_prices))}\n" if available_prices else ""
                msg = (
                    f"🎹 阿格麗希釋票速報！\n\n"
                    f"{title}\n"
                    f"📍{venue_name}\n\n"
                    f"🎫 剩餘票數：約 {total_remaining} 張\n"
                    f"{price_text}\n"
                    f"快去 OPENTIX 搶票：\n"
                    f"https://www.opentix.life/event/{event_id}"
                )
                send_line_message(msg)
                NOTIFIED_EVENTS.add(event_id)
            else:
                print(f"[{venue_name}] 仍有票，已於本輪推播過跳過。", flush=True)
        else:
            if event_id in NOTIFIED_EVENTS:
                print(f"[{venue_name}] 票券已搶完，重置通知狀態。", flush=True)
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

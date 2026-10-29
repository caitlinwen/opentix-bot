import os
import time
import requests

EVENT_IDS = [
    "2076925048527581185",  # 台北場
    "2079132570898259969",  # 高雄場
    "2072537230141886465",  # 屏東場
]

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
        print(f"Push status: {res.status_code}", flush=True)
        if res.status_code != 200:
            print(f"LINE error details: {res.text}", flush=True)
    except Exception as e:
        print(f"Failed to push LINE message: {e}", flush=True)

def format_alert(title, venue, date_str, price, available_count, event_id):
    return (
        f"🎹 阿格麗希釋票速報！\n\n"
        f"{title}\n"
        f"📍{venue}\n"
        f"{date_str}\n\n"
        f"🎟️ {price} 元 | 剩餘 {available_count} 張\n\n"
        f"快去 OPENTIX 搶票：\n"
        f"https://www.opentix.life/event/{event_id}"
    )

def check_event(event_id):
    api_url = f"https://www.opentix.life/oapi/api/v1/events/{event_id}"
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)"
    }
    
    try:
        response = requests.get(api_url, headers=headers, timeout=10)
        data = response.json()
    except Exception as e:
        print(f"Error fetching {event_id}: {e}", flush=True)
        return

    title = data.get("title", "瑪莎·阿格麗希音樂會")
    for perf in data.get("performances", []):
        venue = perf.get("venue", {}).get("name", "音樂廳")
        start_time = perf.get("startDateTime", "")

        for plan in perf.get("pricePlans", []):
            remaining = plan.get("remainingTickets", 0)
            price = plan.get("price", 0)

            if remaining > 0:
                print(f"[{venue}] 發現釋票: {price} 元, 剩餘 {remaining} 張！", flush=True)
                msg = format_alert(title, venue, start_time, price, remaining, event_id)
                send_line_message(msg)

def poll_for_duration(minutes=10, interval=20):
    end_time = time.time() + (minutes * 60)
    print(f"Starting cloud monitoring loop ({interval}s interval for {minutes}m)...", flush=True)
    
    while time.time() < end_time:
        for eid in EVENT_IDS:
            check_event(eid)
        time.sleep(interval)

# --- ONE-TIME DIRECT TEST ---
if __name__ == "__main__":
    print("Testing LINE connection now...", flush=True)
    msg = format_alert(
        "瑪莎·阿格麗希鋼琴獨奏會",
        "台北・國家音樂廳",
        "11/12 (四) 19:30",
        "1200",
        1,
        "2076925048527581185"
    )
    send_line_message(msg)
    print("Test run completed.", flush=True)

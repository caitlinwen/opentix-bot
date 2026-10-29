import os
import time
import requests

EVENT_IDS = [
    "2076925048527581185",  # 台北場
    "2079132570898259969",  # 高雄場
    "2072537230141886465",  # 屏東場
]

LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_USER_ID = os.getenv("LINE_USER_ID")

def send_line_message(text_content):
    if not LINE_CHANNEL_ACCESS_TOKEN or not LINE_USER_ID:
        print("Missing LINE credentials.")
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
    res = requests.post(url, json=payload, headers=headers)
    print(f"Notification status: {res.status_code}")

def format_alert(title, venue, date_str, price, available_count, event_id):
    return (
        f"🦮🐕 汪汪汪！阿格麗希獵犬聞到了票的味道了！\n\n"
        f"{title}\n"
        f"📍{venue}\n"
        f"{date_str}\n\n"
        f"🎟️ {price} | {available_count} 張\n\n"
        f"一般可購買座位：{available_count} 張\n\n"
        f"快去 OPENTIX 搶票！\n"
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
        print(f"Error fetching {event_id}: {e}")
        return

    title = data.get("title", "瑪莎·阿格麗希音樂會")
    for perf in data.get("performances", []):
        venue = perf.get("venue", {}).get("name", "音樂廳")
        start_time = perf.get("startDateTime", "")

        for plan in perf.get("pricePlans", []):
            remaining = plan.get("remainingTickets", 0)
            price = plan.get("price", 0)
            
            if remaining > 0:
                print(f"Ticket found at {venue}: NT${price} ({remaining} seats)")
                msg = format_alert(title, venue, start_time, price, remaining, event_id)
                send_line_message(msg)

def poll_for_duration(minutes=10, interval=20):
    """Polls repeatedly for the specified duration before cleanly terminating."""
    end_time = time.time() + (minutes * 60)
    print(f"Starting cloud monitoring loop ({interval}s interval for {minutes}m)...")
    
    while time.time() < end_time:
        for eid in EVENT_IDS:
            check_event(eid)
        time.sleep(interval)

if __name__ == "__main__":
    # If LOOP_MINUTES is provided, loop in the cloud; otherwise run once
    loop_mins = int(os.getenv("LOOP_MINUTES", "0"))
    if loop_mins > 0:
        poll_for_duration(minutes=loop_mins, interval=20)
    else:
        for eid in EVENT_IDS:
            check_event(eid)

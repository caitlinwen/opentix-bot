import os
import requests

# 監控的三個場次 ID（台北、高雄、屏東）
EVENT_IDS = [
    "2076925048527581185",  # 台北場 
    "2079132570898259969",  # 高雄場 
    "2072537230141886465",  # 屏東場
]

LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_USER_ID = os.getenv("LINE_USER_ID")

def send_line_message(text_content):
    if not LINE_CHANNEL_ACCESS_TOKEN or not LINE_USER_ID:
        print("未設定 LINE 憑證。")
        return

    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"
    }
    payload = {
        "to": LINE_USER_ID,
        "messages": [
            {
                "type": "text",
                "text": text_content
            }
        ]
    }
    res = requests.post(url, json=payload, headers=headers)
    print(f"發送狀態碼: {res.status_code}")

def format_alert(title, venue, date_str, price, available_count, event_id):
    # 排版格式比照截圖樣式
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
        print(f"獲取活動 {event_id} 失敗: {e}")
        return

    # 動態取得活動標題
    title = data.get("title", "瑪莎·阿格麗希音樂會")

    # 巡歷每場演出與票價層級
    for perf in data.get("performances", []):
        # 取得場館與時間
        venue = perf.get("venue", {}).get("name", "音樂廳")
        start_time = perf.get("startDateTime", "")

        for plan in perf.get("pricePlans", []):
            remaining = plan.get("remainingTickets", 0)
            price = plan.get("price", 0)
            
            # 若有可購買票券，立即發送 LINE 通知
            if remaining > 0:
                print(f"[{venue}] 發現票券: {price} 元, 剩餘 {remaining} 張")
                msg = format_alert(title, venue, start_time, price, remaining, event_id)
                send_line_message(msg)

def main():
    for event_id in EVENT_IDS:
        check_event(event_id)

if __name__ == "__main__":
    main()

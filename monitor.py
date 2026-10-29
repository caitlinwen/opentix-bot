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

# 記錄已發送通知的場次，避免同一輪內每 20 秒重複轟炸
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

        title_match = re.search(r'<title>(.*?)</title>', html)
        title = title_match.group(1).split('|')[0].strip() if title_match else "瑪莎·阿格麗希音樂會"

        # 檢測是否有明確的剩餘票數（數字大於 0）
        remaining_matches = re.findall(r'remainingTickets["\']?\s*:\s*(\d+)', html)
        has_positive_remaining = any(int(c) > 0 for c in remaining_matches)

        # 檢測頁面按鈕是否為「立即購票」且未完全售完
        # OPENTIX 全售完時頁面通常會出現「已售完」或全部方案被加上 block_soldOut
        is_sold_out_banner = "已售罄" in html or "已售完" in html
        is_instock_schema = bool(re.search(r'"availability"\s*:\s*"(?:https?://schema\.org/)?InStock"', html))
        # 嚴格判定：只有當真正抓到剩餘張數 > 0 時才視為釋票
        is_available = has_positive_remaining

        print(f"Checked [{venue_name}] - InStockSchema: {is_instock_schema}, SoldOutText: {is_sold_out_banner}, TicketsFound: {has_positive_remaining}", flush=True)

        if is_available:
            # 防重複機制：該場次如果已經推播過，就不再重複發送
            if event_id not in NOTIFIED_EVENTS:
                print(f"🚨 [{venue_name}] 偵測到釋票！發送 LINE 通知...", flush=True)
                msg = format_alert(title, venue_name, event_id, "🎟️ 系統偵測到有票券釋出！")
                send_line_message(msg)
                NOTIFIED_EVENTS.add(event_id)
            else:
                print(f"[{venue_name}] 仍有票，但已於本輪發送過推播，跳過避免洗版。", flush=True)
        else:
            # 如果票被搶走了，重置通知狀態，下次又有票時才能再次通知
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

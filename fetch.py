import requests
import json
import os
import time
from datetime import datetime, timezone, timedelta

tw_tz = timezone(timedelta(hours=8))
timestamp = datetime.now(tw_tz).strftime("%m%d%H%M")

# --- 設定區 ---
CLIENT_ID = 'b11901018-81457f6f-e1ce-47fa'
CLIENT_SECRET = 'c8e6a43e-6a54-407f-911f-8c7a69070aee'
TOKEN_CACHE_FILE = 'data/tdx_token.json'  # 暫存 Token 的檔案

def get_valid_token():
    """取得有效的 Token（優先從暫存讀取，過期才重新申請）"""
    
    # 1. 檢查是否有暫存檔
    if os.path.exists(TOKEN_CACHE_FILE):
        with open(TOKEN_CACHE_FILE, 'r') as f:
            token_data = json.load(f)
            
        # 檢查是否過期 (預留 60 秒緩衝，避免邊緣失效)
        if time.time() < token_data.get('expires_at', 0) - 60:
            print(">>> 使用暫存的 Token (尚未過期)")
            return token_data.get('access_token')

    # 2. 如果檔案不存在或已過期，則重新申請
    print(">>> Token 已過期或不存在，重新申請中...")
    auth_url = "https://tdx.transportdata.tw/auth/realms/TDXConnect/protocol/openid-connect/token"
    auth_data = {
        'grant_type': 'client_credentials',
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET
    }
    
    try:
        start_time = time.time()
        response = requests.post(auth_url, data=auth_data)
        response.raise_for_status()
        res_json = response.json()
        
        access_token = res_json.get('access_token')
        expires_in = res_json.get('expires_in') # TDX 回傳的有效秒數
        
        # 儲存 Token 與過期時間戳記
        cache_data = {
            'access_token': access_token,
            'expires_at': start_time + expires_in
        }
        with open(TOKEN_CACHE_FILE, 'w') as f:
            json.dump(cache_data, f)
            
        return access_token
    except Exception as e:
        print(f"取得新 Token 失敗: {e}")
        return None

def fetch_tra_data():
    """主程式：獲取資料"""
    token = get_valid_token()
    if not token:
        print("無法取得授權，程式終止。")
        return
    
    # 指定[日期]之臺鐵所有車次時刻表資料
    # date = "2026-05-20"
    # api_url = f"https://tdx.transportdata.tw/api/basic/v3/Rail/TRA/DailyTrainTimetable/TrainDate/{date}"

    # 臺鐵列車即時位置動態資料
    api_url = "https://tdx.transportdata.tw/api/basic/v3/Rail/TRA/TrainLiveBoard?$format=JSON"

    # 臺鐵列車即時到離站資料
    # api_url = "https://tdx.transportdata.tw/api/basic/v3/Rail/TRA/StationLiveBoard?$format=JSON"

    headers = {'Authorization': f'Bearer {token}'}
    
    try:
        print("開始請求台鐵時刻表資料...")
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()
        
        # 儲存資料
        with open(f'data/data_{timestamp}.json', 'w', encoding='utf-8') as f:
            json.dump(response.json(), f, ensure_ascii=False, indent=4)
        print("資料儲存成功！")
        
    except Exception as e:
        print(f"請求資料失敗: {e}")

if __name__ == "__main__":
    fetch_tra_data()

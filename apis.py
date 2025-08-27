import requests
import traceback

def autopost_video(platform, filepath, caption, config):
    """
    Main autopost handler for all platforms
    Returns: (log, posted_url)
    """
    try:
        if platform == "telegram":
            return post_telegram(filepath, caption, config)
        elif platform == "youtube":
            return post_youtube(filepath, caption, config)
        elif platform == "instagram":
            return post_instagram(filepath, caption, config)
        elif platform == "tiktok":
            return post_tiktok(filepath, caption, config)
        else:
            return ("Unknown platform", "")
    except Exception as e:
        return (f"❌ Exception: {str(e)}\n{traceback.format_exc()}", "")

def post_telegram(filepath, caption, config):
    url = f"https://api.telegram.org/bot{config['telegram']['bot_token']}/sendVideo"
    params = {
        "chat_id": config['telegram']['chat_id'],
        "caption": caption
    }
    files = {"video": open(filepath, "rb")}
    resp = requests.post(url, data=params, files=files)
    res_json = resp.json()
    if res_json.get("ok"):
        msg = res_json['result']
        posted_url = f"https://t.me/{config['telegram']['channel_username']}/{msg['message_id']}"
        return ("✅ Telegram posted", posted_url)
    else:
        return (f"❌ Telegram error: {resp.text}", "")

def post_youtube(filepath, caption, config):
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload
        import pickle
        import os.path

        SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
        creds = None
        token_pickle = "token.pickle"
        # Use pickle to save credentials
        if os.path.exists(token_pickle):
            with open(token_pickle, "rb") as token:
                creds = pickle.load(token)
        else:
            flow = InstalledAppFlow.from_client_secrets_file(config["youtube"]["client_secrets"], SCOPES)
            creds = flow.run_local_server(port=8080)
            with open(token_pickle, "wb") as token:
                pickle.dump(creds, token)
        youtube = build("youtube", "v3", credentials=creds)
        body=dict(
            snippet=dict(
                title=caption[:100],
                description=caption,
                tags=[],
                categoryId="22"
            ),
            status=dict(
                privacyStatus="public"
            )
        )
        media = MediaFileUpload(filepath, chunksize=-1, resumable=True, mimetype="video/*")
        req = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
        resp = req.execute()
        url = f"https://youtube.com/watch?v={resp['id']}"
        return ("✅ YouTube posted", url)
    except Exception as e:
        return (f"❌ YouTube error: {str(e)}", "")

def post_instagram(filepath, caption, config):
    try:
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.chrome.options import Options
        import time
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=800,600")
        chrome_options.add_argument(f"user-data-dir={config['instagram']['profile_dir']}")
        driver = webdriver.Chrome(options=chrome_options, executable_path=config['instagram']['chromedriver_path'])
        driver.get("https://www.instagram.com/")
        time.sleep(5)
        # Upload logic (UI changes often, may require update if IG changes layout)
        upload_btn = driver.find_element(By.XPATH, "//div[@role='menuitem']")
        upload_btn.click()
        time.sleep(2)
        file_input = driver.find_element(By.XPATH, "//input[@type='file']")
        file_input.send_keys(filepath)
        time.sleep(5)
        next_btn = driver.find_element(By.XPATH, "//button[text()='Next']")
        next_btn.click()
        time.sleep(2)
        caption_box = driver.find_element(By.XPATH, "//textarea")
        caption_box.send_keys(caption)
        share_btn = driver.find_element(By.XPATH, "//button[text()='Share']")
        share_btn.click()
        time.sleep(10)
        driver.quit()
        return ("✅ Instagram posted", "")
    except Exception as e:
        return (f"❌ Instagram error: {str(e)}", "")

def post_tiktok(filepath, caption, config):
    try:
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.chrome.options import Options
        import time
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=800,600")
        chrome_options.add_argument(f"user-data-dir={config['tiktok']['profile_dir']}")
        driver = webdriver.Chrome(options=chrome_options, executable_path=config['tiktok']['chromedriver_path'])
        driver.get("https://www.tiktok.com/upload")
        time.sleep(8)
        file_input = driver.find_element(By.XPATH, "//input[@type='file']")
        file_input.send_keys(filepath)
        time.sleep(10)
        caption_box = driver.find_element(By.XPATH, "//textarea")
        caption_box.send_keys(caption)
        post_btn = driver.find_element(By.XPATH, "//button[contains(., 'Post') or contains(., 'Upload')]")
        post_btn.click()
        time.sleep(10)
        driver.quit()
        return ("✅ TikTok posted", "")
    except Exception as e:
        return (f"❌ TikTok error: {str(e)}", "")

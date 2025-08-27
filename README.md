# SMM Autoposter (YouTube, Instagram, TikTok, Telegram)

## Features

- Private login dashboard (Flask)
- Bulk video upload, scheduling, and auto posting
- Fully working Telegram, YouTube, Instagram, TikTok posting (PC required for IG/TT/YT)
- Data saved to SQLite, logs and status in dashboard

---

## Setup (Windows/PC)

### 1. Install Python packages

```bash
pip install flask requests selenium google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

### 2. ChromeDriver

- Download [ChromeDriver](https://chromedriver.chromium.org/downloads) matching your Chrome version.
- Place `chromedriver.exe` in `C:/chromedriver.exe` or update the path in `config.json`.

### 3. Prepare Instagram & TikTok browser profiles

- Let the script create folders (`C:/ig-profile`, `C:/tt-profile`) or create them manually.
- First run: run with `chrome_options.add_argument("--headless")` *removed* in `apis.py`.
- Log in manually to your IG/TT account in the launched browser.
- After login, close the window and restore `--headless` in the code.
- Now your session is saved and autoposting is fully automatic.

### 4. YouTube API

- Set up a Google Cloud project.
- Enable YouTube Data API.
- Download `client_secret.json` and put path in `config.json`.
- First run: you’ll be prompted to log in via browser, then `token.pickle` is saved for future use.

### 5. Edit `config.json`

- Fill in your credentials and paths as explained above.

### 6. Run the Server

```bash
python file.py
```

- Access your dashboard at `http://localhost:5000`

---

## Supported Platforms

- **Telegram:** Posts via Bot API (edit `bot_token`, `chat_id`).
- **YouTube:** Posts via Google API (edit `client_secrets`, do 1-time login).
- **Instagram/TikTok:** Posts via Selenium (edit `chromedriver_path`, login 1-time to save session).
- **Everything is saved to SQLite and works from the web dashboard.**

---

## Troubleshooting

- If IG/TT posting fails, run with `--headless` removed and log in manually.
- If YouTube posting fails, check Google API credentials and consent.
- For any Selenium "no element found" errors: UI may have changed, update XPATHs in `apis.py`.

---

## Security

- This is for **private use** only.
- Do **not** expose the Flask server to the internet.

---

## Extend

- Add more platforms by extending `apis.py`.

---

**Need help? Just ask!**

import os
import json
import sqlite3
import threading
import time
from datetime import datetime, timedelta
from flask import Flask, request, render_template_string, redirect, url_for, session, send_from_directory, flash
from werkzeug.utils import secure_filename
from apis import autopost_video

CONFIG_FILE = "config.json"
UPLOAD_FOLDER = "uploads"
DB_FILE = "smm.db"
ALLOWED_EXTENSIONS = {'mp4', 'mov', 'avi', 'mkv'}

def load_config():
    if not os.path.exists(CONFIG_FILE):
        raise Exception("config.json not found! Please create it.")
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

config = load_config()

app = Flask(__name__)
app.secret_key = config["flask_secret"]
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS videos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT NOT NULL,
        caption TEXT,
        scheduled_time DATETIME,
        status TEXT DEFAULT 'pending',
        platform TEXT,
        log TEXT,
        posted_url TEXT
    )""")
    conn.commit()
    conn.close()

init_db()

def check_login(user, pwd):
    return user == config["login"]["username"] and pwd == config["login"]["password"]

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_db():
    return sqlite3.connect(DB_FILE)

@app.route("/", methods=["GET", "POST"])
def login():
    if "user" in session:
        return redirect(url_for("dashboard"))
    error = None
    if request.method == "POST":
        if check_login(request.form["username"], request.form["password"]):
            session["user"] = request.form["username"]
            return redirect(url_for("dashboard"))
        else:
            error = "Invalid credentials"
    return render_template_string(LOGIN_PAGE, error=error)

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM videos ORDER BY id DESC")
    videos = c.fetchall()
    conn.close()
    return render_template_string(DASHBOARD_PAGE, videos=videos, user=session["user"])

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/upload", methods=["POST"])
def upload():
    if "user" not in session:
        return redirect(url_for("login"))
    files = request.files.getlist("videos")
    captions = request.form.getlist("captions")
    platforms = request.form.getlist("platforms")
    scheduled_time = request.form["scheduled_time"]
    if not files:
        flash("No files selected")
        return redirect(url_for("dashboard"))
    for idx, file in enumerate(files):
        if file and allowed_file(file.filename):
            filename = secure_filename(f"{int(time.time())}_{file.filename}")
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(save_path)
            caption = captions[idx] if idx < len(captions) else ""
            for platform in platforms:
                conn = get_db()
                c = conn.cursor()
                c.execute("INSERT INTO videos (filename, caption, scheduled_time, platform) VALUES (?, ?, ?, ?)",
                          (filename, caption, scheduled_time, platform))
                conn.commit()
                conn.close()
    return redirect(url_for("dashboard"))

@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

def scheduler_loop():
    while True:
        now = datetime.now()
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT id, filename, caption, scheduled_time, platform FROM videos WHERE status='pending'")
        videos = c.fetchall()
        for vid in videos:
            vid_id, filename, caption, sch_time, platform = vid
            sch_dt = datetime.strptime(sch_time, "%Y-%m-%dT%H:%M")
            if now >= sch_dt:
                c.execute("UPDATE videos SET status='posting' WHERE id=?", (vid_id,))
                conn.commit()
                threading.Thread(target=post_video, args=(vid_id, filename, caption, platform)).start()
        conn.close()
        time.sleep(30)

def post_video(video_id, filename, caption, platform):
    log, posted_url = autopost_video(
        platform=platform,
        filepath=os.path.join(UPLOAD_FOLDER, filename),
        caption=caption,
        config=config
    )
    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE videos SET status=?, log=?, posted_url=? WHERE id=?", ("posted", log, posted_url, video_id))
    conn.commit()
    conn.close()

LOGIN_PAGE = """
<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><title>SMM Login</title>
<style>
body { background: #1B365D; color:white; font-family:sans-serif; display:flex; flex-direction:column; align-items:center; justify-content:center; height:100vh;}
form { background: #222; padding:30px; border-radius: 14px;}
input { padding:8px; margin:5px 0; width:100%; border-radius:5px;}
button { background:#D4AF37; border:none; padding:10px 20px; border-radius:6px; font-weight:bold;}
</style>
</head>
<body>
<h2>Login to SMM Panel</h2>
<form method="post">
    <input type="text" name="username" placeholder="Username" required><br/>
    <input type="password" name="password" placeholder="Password" required><br/>
    <button type="submit">Login</button>
    {% if error %}<div style="color:crimson;">{{error}}</div>{% endif %}
</form>
</body>
</html>
"""

DASHBOARD_PAGE = """
<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><title>SMM Dashboard</title>
<style>
body { background: #111; color:white; font-family:sans-serif;}
a, button { background:#D4AF37; color:#1B365D; border:none; padding:7px 15px; border-radius:5px; font-weight:bold; text-decoration:none;}
.logout { float:right; background:crimson; color:white;}
table { width:100%; background:#1B365D; border-radius:5px;}
td,th { padding:7px; }
tr:nth-child(even) {background:#222;}
</style>
</head>
<body>
<h2>SMM Dashboard <span style="font-size:0.7em;">[{{user}}]</span>
 <a href="{{url_for('logout')}}" class="logout">Logout</a>
</h2>
<h3>Upload Videos (Bulk)</h3>
<form action="{{url_for('upload')}}" method="post" enctype="multipart/form-data">
    <label>Select Videos</label>
    <input type="file" name="videos" multiple required><br/>
    <label>Captions (one per video, comma-separated)</label>
    <input type="text" name="captions" placeholder="caption1,caption2,..."><br/>
    <label>Platforms</label>
    <input type="checkbox" name="platforms" value="telegram" checked>Telegram
    <input type="checkbox" name="platforms" value="youtube">YouTube
    <input type="checkbox" name="platforms" value="tiktok">TikTok
    <input type="checkbox" name="platforms" value="instagram">Instagram <br/>
    <label>Schedule Time (first post):</label>
    <input type="datetime-local" name="scheduled_time" required><br/>
    <button type="submit">Upload & Schedule</button>
</form>
<br/><hr/>
<h3>Video Queue & Log</h3>
<table>
<tr><th>ID</th><th>File</th><th>Caption</th><th>Time</th><th>Platform</th><th>Status</th><th>Log</th><th>Posted Link</th></tr>
{% for v in videos %}
<tr>
<td>{{v[0]}}</td>
<td><a href="{{url_for('uploaded_file', filename=v[1])}}" target="_blank">{{v[1]}}</a></td>
<td>{{v[2]}}</td>
<td>{{v[3]}}</td>
<td>{{v[5]}}</td>
<td>{{v[4]}}</td>
<td><pre>{{v[6]}}</pre></td>
<td>{% if v[7] %}<a href="{{v[7]}}" target="_blank">Link</a>{% endif %}</td>
</tr>
{% endfor %}
</table>
</body></html>
"""

t = threading.Thread(target=scheduler_loop, daemon=True)
t.start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

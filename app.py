import sqlite3
from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime

app = Flask(__name__)

DB_PATH = "data.db"

# ------------------------------------------------------
# 初始化数据库
# ------------------------------------------------------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            card REAL,
            cash REAL,
            total REAL,
            customers INTEGER,
            note TEXT
        )
        """
    )
    conn.commit()
    conn.close()


# ------------------------------------------------------
# 首页 - 当天记录
# ------------------------------------------------------
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        date = request.form.get("date")
        card = float(request.form.get("card") or 0)
        cash = float(request.form.get("cash") or 0)
        customers = int(request.form.get("customers") or 0)
        note = request.form.get("note", "")

        total = card + cash

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute(
            """
            INSERT INTO records (date, card, cash, total, customers, note)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (date, card, cash, total, customers, note),
        )
        conn.commit()
        conn.close()

        return redirect(url_for("history"))

    today = datetime.now().strftime("%Y-%m-%d")
    return render_template("index.html", today=today)


# ------------------------------------------------------
# 历史记录页面
# ------------------------------------------------------
@app.route("/history")
def history():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        """
        SELECT id, date, card, cash, total, customers, note
        FROM records
        ORDER BY date DESC, id DESC
        """
    )
    rows = c.fetchall()
    conn.close()
    return render_template("history.html", rows=rows)


# ------------------------------------------------------
# 删除记录功能
# ------------------------------------------------------
@app.route("/delete/<int:record_id>", methods=["POST"])
def delete_record(record_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM records WHERE id = ?", (record_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("history"))


# ------------------------------------------------------
# 导出 CSV（保留原功能，如无则忽略）
# ------------------------------------------------------
@app.route("/export")
def export_csv():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM records")
    rows = c.fetchall()
    conn.close()

    csv = "id,date,card,cash,total,customers,note\n"
    for r in rows:
        line = ",".join([str(x) for x in r]) + "\n"
        csv += line

    return csv, 200, {"Content-Type": "text/csv"}


# ------------------------------------------------------
# 启动前初始化数据库
# ------------------------------------------------------
if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)
@app.route("/stats")
def stats():
    return "<h2>统计图表功能即将上线</h2>"

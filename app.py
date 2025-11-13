"""
Main Flask application for Massage Shop Daily Report system.
"""
from flask import Flask, render_template, request, redirect, url_for, flash, send_file, Response
from datetime import datetime, date
import io
import csv
import db  # custom database helper module

app = Flask(__name__)
app.secret_key = "change-this-secret-key"  # change for production

DB_PATH = "data.db"

# Initialize database (create table if not exists)
db.init_db(DB_PATH)


@app.route("/", methods=["GET", "POST"])
def index():
    """
    Today's record page (or selected date).
    GET: show form, prefill with today's record if exists.
    POST: save record for chosen date.
    """
    if request.method == "POST":
        # Read form values
        form_date = request.form.get("date") or date.today().isoformat()
        card_amount = request.form.get("card_amount") or "0"
        cash_amount = request.form.get("cash_amount") or "0"
        customer_count = request.form.get("customer_count") or "0"
        note = request.form.get("note") or ""

        # Validate and convert
        try:
            # allow empty or invalid numeric input to be treated as 0
            card_amount_f = float(card_amount)
            cash_amount_f = float(cash_amount)
            customer_count_i = int(customer_count)
        except ValueError:
            flash("请输入有效的数字（刷卡金额、现金金额为数字，客人数为整数）", "danger")
            return redirect(url_for("index"))

        total = round(card_amount_f + cash_amount_f, 2)

        # Insert or update the record for that date
        db.upsert_record(DB_PATH,
                         form_date,
                         card_amount_f,
                         cash_amount_f,
                         total,
                         customer_count_i,
                         note)
        flash(f"{form_date} 的记录已保存。", "success")
        return redirect(url_for("index", date=form_date))

    # GET
    q_date = request.args.get("date")
    if not q_date:
        q_date = date.today().isoformat()

    record = db.get_record_by_date(DB_PATH, q_date)
    if record:
        # record is a dict
        initial = record
    else:
        initial = {
            "date": q_date,
            "card_amount": 0.0,
            "cash_amount": 0.0,
            "total_amount": 0.0,
            "customer_count": 0,
            "note": ""
        }

    return render_template("index.html", record=initial)


@app.route("/history")
def history():
    """
    History page: list records with filtering and sorting.
    Supports query params:
      - month: YYYY-MM to filter by month
      - start, end: YYYY-MM-DD for range
      - order: asc or desc (date)
    """
    month = request.args.get("month")
    start = request.args.get("start")
    end = request.args.get("end")
    order = request.args.get("order") or "desc"

    if month:
        # construct start and end of month
        try:
            start_date = datetime.strptime(month + "-01", "%Y-%m-%d").date()
            # next month
            if start_date.month == 12:
                end_date = date(start_date.year + 1, 1, 1)
            else:
                end_date = date(start_date.year, start_date.month + 1, 1)
            end_date = (end_date.replace()).isoformat()
            start = start_date.isoformat()
            end = (date.fromisoformat(end_date) - datetime.timedelta(days=1)).isoformat()
        except Exception:
            # ignore and fallback to full list
            start = None
            end = None

    records = db.get_records(DB_PATH, start=start, end=end, order=order)
    return render_template("history.html", records=records, order=order, start=start, end=end, month=month)


@app.route("/stats", methods=["GET", "POST"])
def stats():
    """
    Statistics page: choose time range and show aggregates.
    """
    # default to this month
    if request.method == "POST":
        range_type = request.form.get("range_type")
        start = request.form.get("start")
        end = request.form.get("end")
        if range_type == "custom" and start and end:
            start_date = start
            end_date = end
        elif range_type == "this_month":
            today = date.today()
            start_date = date(today.year, today.month, 1).isoformat()
            # end as today
            end_date = today.isoformat()
        elif range_type == "this_week":
            today = date.today()
            start_of_week = today - datetime.timedelta(days=today.weekday())
            start_date = start_of_week.isoformat()
            end_date = today.isoformat()
        else:
            # fallback: last 30 days
            today = date.today()
            start_date = (today - datetime.timedelta(days=29)).isoformat()
            end_date = today.isoformat()
    else:
        # GET default: this month so far
        today = date.today()
        start_date = date(today.year, today.month, 1).isoformat()
        end_date = today.isoformat()

    # fetch records in range
    records = db.get_records(DB_PATH, start=start_date, end=end_date, order="asc")

    # compute aggregates
    total_card = sum(r["card_amount"] for r in records)
    total_cash = sum(r["cash_amount"] for r in records)
    total_amount = sum(r["total_amount"] for r in records)
    total_customers = sum(r["customer_count"] for r in records)

    # number of days in the range (based on dates present or calendar span?)
    # We'll compute by calendar days between start and end inclusive
    try:
        dstart = date.fromisoformat(start_date)
        dend = date.fromisoformat(end_date)
        days_span = (dend - dstart).days + 1
    except Exception:
        days_span = max(1, len(records))

    avg_daily_income = (total_amount / days_span) if days_span else 0
    avg_daily_customers = (total_customers / days_span) if days_span else 0

    summary = {
        "total_card": round(total_card, 2),
        "total_cash": round(total_cash, 2),
        "total_amount": round(total_amount, 2),
        "total_customers": total_customers,
        "avg_daily_income": round(avg_daily_income, 2),
        "avg_daily_customers": round(avg_daily_customers, 2),
        "days_span": days_span,
        "start_date": start_date,
        "end_date": end_date
    }

    return render_template("stats.html", records=records, summary=summary)


@app.route("/export")
def export_csv():
    """
    Export all records as CSV.
    """
    records = db.get_records(DB_PATH, order="asc")
    # create CSV in memory
    si = io.StringIO()
    cw = csv.writer(si)
    # header
    cw.writerow(["日期", "刷卡金额", "现金金额", "总金额", "客人数", "备注"])
    for r in records:
        cw.writerow([
            r["date"],
            f"{r['card_amount']:.2f}",
            f"{r['cash_amount']:.2f}",
            f"{r['total_amount']:.2f}",
            r["customer_count"],
            r["note"] or ""
        ])
    output = si.getvalue()
    si.close()
    # prepare response
    resp = Response(output, mimetype="text/csv")
    filename = f"massage_records_{date.today().isoformat()}.csv"
    resp.headers["Content-Disposition"] = f"attachment; filename={filename}"
    return resp


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)

"""
Main application views: index, history, stats, therapists management, export, charts.
"""
import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, Response, jsonify
from flask_login import login_required, current_user
from models import db, Record, Therapist
from datetime import datetime, date, timedelta
import io, csv
from sheets import maybe_append_to_sheet
from dateutil.parser import parse as dateparse

main_bp = Blueprint('main', __name__)
# 删除记录
@main_bp.route('/record/<int:rid>/delete', methods=['POST'])
@login_required
def delete_record(rid):
    rec = Record.query.get_or_404(rid)
    db.session.delete(rec)
    db.session.commit()
    flash("记录已删除", "info")
    # 删除后返回历史记录或者当天记录页面
    return redirect(request.referrer or url_for('main.history'))
SERVICE_TYPES = ["Full Body", "Foot", "Combination", "Chair"]
DURATIONS = ["20min", "30min", "40min", "60min"]

def parse_date(s, default=None):
    if not s:
        return default
    try:
        return date.fromisoformat(s)
    except Exception:
        try:
            return dateparse(s).date()
        except Exception:
            return default

@main_bp.route('/')
@login_required
def index():
    q_date = request.args.get('date')
    if q_date:
        d = parse_date(q_date, date.today())
    else:
        d = date.today()
    # show an empty form or last record for that date
    rec = Record.query.filter_by(date=d).first()
    therapists = Therapist.query.filter_by(status='active').all()
    return render_template('index.html', record=rec, date=d, service_types=SERVICE_TYPES, durations=DURATIONS, therapists=therapists)

@main_bp.route('/', methods=['POST'])
@login_required
def save_record():
    # form data
    form_date = request.form.get('date') or date.today().isoformat()
    d = parse_date(form_date, date.today())
    try:
        card_amount = float(request.form.get('card_amount') or 0.0)
        cash_amount = float(request.form.get('cash_amount') or 0.0)
        customer_count = int(request.form.get('customer_count') or 0)
    except ValueError:
        flash("请输入有效的数字", "danger")
        return redirect(url_for('main.index', date=form_date))
    note = request.form.get('note')
    service_type = request.form.get('service_type') or SERVICE_TYPES[0]
    duration = request.form.get('duration') or DURATIONS[0]
    therapist_id = request.form.get('therapist_id') or None
    if therapist_id == '': therapist_id = None

    total = round(card_amount + cash_amount, 2)

    # create a new record (each save creates a record row)
    rec = Record(
        date=d,
        card_amount=card_amount,
        cash_amount=cash_amount,
        total_amount=total,
        customer_count=customer_count,
        note=note,
        service_type=service_type,
        duration=duration,
        therapist_id=int(therapist_id) if therapist_id else None
    )
    db.session.add(rec)
    db.session.commit()

    # optional Google Sheets backup
    try:
        maybe_append_to_sheet(rec)
    except Exception as e:
        # do not block saving, log to console (server logs)
        print("Google Sheets backup failed:", e)

    flash("记录已保存", "success")
    return redirect(url_for('main.index', date=d.isoformat()))

@main_bp.route('/history')
@login_required
def history():
    # filtering
    start = request.args.get('start')
    end = request.args.get('end')
    service = request.args.get('service')
    therapist = request.args.get('therapist')
    order = request.args.get('order') or 'desc'
    page = int(request.args.get('page') or 1)
    per_page = 20

    q = Record.query
    if start:
        dstart = parse_date(start)
        if dstart:
            q = q.filter(Record.date >= dstart)
    if end:
        dend = parse_date(end)
        if dend:
            q = q.filter(Record.date <= dend)
    if service:
        q = q.filter(Record.service_type == service)
    if therapist:
        # allow name search
        q = q.join(Therapist).filter(Therapist.name.ilike(f"%{therapist}%"))

    q = q.order_by(Record.date.desc() if order == 'desc' else Record.date.asc())
    pagination = q.paginate(page=page, per_page=per_page, error_out=False)
    therapists = Therapist.query.all()
    return render_template('history.html', records=pagination.items, pagination=pagination, service_types=SERVICE_TYPES, therapists=therapists, filters={'start':start,'end':end,'service':service,'therapist':therapist,'order':order})

@main_bp.route('/export')
@login_required
def export_csv():
    # export current filtered set or all
    start = request.args.get('start')
    end = request.args.get('end')
    q = Record.query
    if start:
        dstart = parse_date(start)
        if dstart:
            q = q.filter(Record.date >= dstart)
    if end:
        dend = parse_date(end)
        if dend:
            q = q.filter(Record.date <= dend)
    q = q.order_by(Record.date.asc())
    records = q.all()

    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(["日期","服务项目","时长","技师","刷卡金额","现金金额","总金额","客人数","备注","创建时间"])
    for r in records:
        therapist_name = r.therapist.name if r.therapist else ""
        cw.writerow([r.date.isoformat(), r.service_type, r.duration, therapist_name, f"{r.card_amount:.2f}", f"{r.cash_amount:.2f}", f"{r.total_amount:.2f}", r.customer_count, r.note or "", r.created_at.isoformat()])
    output = si.getvalue()
    si.close()
    filename = f"records_{date.today().isoformat()}.csv"
    resp = Response(output, mimetype="text/csv")
    resp.headers["Content-Disposition"] = f"attachment; filename={filename}"
    return resp

@main_bp.route('/therapists')
@login_required
def therapists():
    list_all = Therapist.query.order_by(Therapist.name.asc()).all()
    return render_template('therapists.html', therapists=list_all)

@main_bp.route('/therapists/new', methods=['GET','POST'])
@login_required
def therapist_new():
    if request.method == 'POST':
        name = request.form.get('name').strip()
        if not name:
            flash("请输入技师姓名", "danger")
            return redirect(url_for('main.therapist_new'))
        t = Therapist(name=name, status=request.form.get('status','active'), commission_rate=float(request.form.get('commission_rate') or 0.0))
        db.session.add(t)
        db.session.commit()
        flash("技师已新增", "success")
        return redirect(url_for('main.therapists'))
    return render_template('therapist_form.html', therapist=None)

@main_bp.route('/therapists/<int:tid>/edit', methods=['GET','POST'])
@login_required
def therapist_edit(tid):
    t = Therapist.query.get_or_404(tid)
    if request.method == 'POST':
        t.name = request.form.get('name').strip()
        t.status = request.form.get('status','active')
        t.commission_rate = float(request.form.get('commission_rate') or 0.0)
        db.session.commit()
        flash("技师信息已更新", "success")
        return redirect(url_for('main.therapists'))
    return render_template('therapist_form.html', therapist=t)

@main_bp.route('/stats', methods=['GET','POST'])
@login_required
def stats():
    if request.method == 'POST':
        range_type = request.form.get('range_type')
        start = request.form.get('start')
        end = request.form.get('end')
        if range_type == 'this_month':
            today = date.today()
            start_date = date(today.year, today.month, 1)
            end_date = today
        elif range_type == 'this_week':
            today = date.today()
            start_date = today - timedelta(days=today.weekday())
            end_date = today
        elif range_type == 'custom' and start and end:
            start_date = parse_date(start)
            end_date = parse_date(end)
        else:
            # last 30 days
            end_date = date.today()
            start_date = end_date - timedelta(days=29)
    else:
        today = date.today()
        start_date = date(today.year, today.month, 1)
        end_date = date.today()

    records = Record.query.filter(Record.date >= start_date, Record.date <= end_date).order_by(Record.date.asc()).all()
    total_card = sum(r.card_amount for r in records)
    total_cash = sum(r.cash_amount for r in records)
    total_amount = sum(r.total_amount for r in records)
    total_customers = sum(r.customer_count for r in records)
    days_span = max(1, (end_date - start_date).days + 1)
    avg_daily_income = round(total_amount / days_span, 2)
    avg_daily_customers = round(total_customers / days_span, 2)

    # per therapist summary (simple)
    therapist_summaries = {}
    for r in records:
        key = r.therapist.name if r.therapist else "未指定"
        ts = therapist_summaries.setdefault(key, {"count":0,"revenue":0.0})
        ts["count"] += 1
        ts["revenue"] += r.total_amount

    # per service summary
    service_summary = {}
    for r in records:
        key = r.service_type or "其他"
        ss = service_summary.setdefault(key, {"count":0,"revenue":0.0})
        ss["count"] += 1
        ss["revenue"] += r.total_amount

    return render_template('stats.html',
                           summary={
                               "total_card": round(total_card,2),
                               "total_cash": round(total_cash,2),
                               "total_amount": round(total_amount,2),
                               "total_customers": total_customers,
                               "avg_daily_income": avg_daily_income,
                               "avg_daily_customers": avg_daily_customers,
                               "days_span": days_span,
                               "start_date": start_date.isoformat(),
                               "end_date": end_date.isoformat()
                           },
                           records=records,
                           therapist_summaries=therapist_summaries,
                           service_summary=service_summary)

@main_bp.route('/chart/income')
@login_required
def chart_income():
    # params
    start = request.args.get('start')
    end = request.args.get('end')
    if start and end:
        start_date = parse_date(start)
        end_date = parse_date(end)
    else:
        end_date = date.today()
        start_date = end_date - timedelta(days=29)
    # aggregate daily totals
    days = (end_date - start_date).days + 1
    labels = []
    data = []
    for i in range(days):
        d = start_date + timedelta(days=i)
        s = db.session.query(db.func.sum(Record.total_amount)).filter(Record.date==d).scalar() or 0.0
        labels.append(d.isoformat())
        data.append(round(s,2))
    return jsonify({"labels": labels, "data": data})

@main_bp.route('/chart/service')
@login_required
def chart_service():
    start = request.args.get('start')
    end = request.args.get('end')
    if start and end:
        start_date = parse_date(start)
        end_date = parse_date(end)
    else:
        end_date = date.today()
        start_date = end_date - timedelta(days=29)
    q = db.session.query(Record.service_type, db.func.sum(Record.total_amount)).filter(Record.date >= start_date, Record.date <= end_date).group_by(Record.service_type).all()
    labels = [r[0] for r in q]
    data = [round(r[1] or 0.0,2) for r in q]
    return jsonify({"labels": labels, "data": data})

@main_bp.route('/chart/therapist')
@login_required
def chart_therapist():
    start = request.args.get('start')
    end = request.args.get('end')
    if start and end:
        start_date = parse_date(start)
        end_date = parse_date(end)
    else:
        end_date = date.today()
        start_date = end_date - timedelta(days=29)
    q = db.session.query(Therapist.name, db.func.sum(Record.total_amount)).join(Record, Therapist.id==Record.therapist_id).filter(Record.date >= start_date, Record.date <= end_date).group_by(Therapist.name).all()
    labels = [r[0] for r in q]
    data = [round(r[1] or 0.0,2) for r in q]
    return jsonify({"labels": labels, "data": data})
@main_bp.route('/record/<int:rid>/delete', methods=['POST'])
@login_required
def delete_record(rid):
    rec = Record.query.get_or_404(rid)
    db.session.delete(rec)
    db.session.commit()
    flash("记录已删除", "info")
    return redirect(url_for('main.index'))

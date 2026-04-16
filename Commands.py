import os
from datetime import datetime, date
from openpyxl import load_workbook

from Constants import EXCEL_FILE, LOG_SHEET, TARGET_HOURS
from Workbook import create_workbook, format_log_row, find_open_session, read_log
from Summary import build_summary


def cmd_start(time_override=None):
    if not os.path.exists(EXCEL_FILE):
        create_workbook()

    wb = load_workbook(EXCEL_FILE)
    ws = wb[LOG_SHEET]

    open_row = find_open_session(ws)
    if open_row:
        t = ws.cell(row=open_row, column=3).value
        print(f"⚠  Session already running since {t}. Use 'pause' or 'stop' first.")
        return

    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = time_override or now.strftime("%H:%M")
    row = ws.max_row + 1

    ws.cell(row=row, column=1, value=date_str)
    ws.cell(row=row, column=2, value=f'=WEEKNUM(A{row})')
    ws.cell(row=row, column=3, value=time_str)
    ws.cell(row=row, column=4, value=None)
    ws.cell(row=row, column=5, value=f'=IF(D{row}<>"",ROUND((D{row}-C{row})*24, 2),"")')
    format_log_row(ws, row)  # sets formats AND writes the week formula

    note = " (manually set)" if time_override else ""
    wb.save(EXCEL_FILE)
    print(f"▶  Started at {time_str} on {date_str}{note}")


def cmd_pause(time_override=None):
    _close_session(time_override)


def cmd_stop(time_override=None):
    wb, ws = _close_session(time_override)
    if wb is None:
        return

    _print_day_summary(ws)
    print("🔄  Rebuilding Summary sheet…")
    build_summary(wb)
    wb.save(EXCEL_FILE)
    print(f"✅  Done — Summary updated in the 'Summary' tab.")


def cmd_status():
    if not os.path.exists(EXCEL_FILE):
        print("No timetracker file found. Run 'start' first.")
        return

    wb = load_workbook(EXCEL_FILE)
    ws = wb[LOG_SHEET]

    today_str = date.today().strftime("%Y-%m-%d")
    now = datetime.now()
    days = read_log(ws)
    info = days.get(today_str)
    open_row = find_open_session(ws)

    # Hours already logged in completed sessions today
    completed_hours = info["total"] if info else 0.0
    completed_sessions = info["sessions"] if info else []

    # If there's an active session, calculate its running duration
    active_start = None
    active_hours = 0.0
    if open_row:
        raw = ws.cell(row=open_row, column=3).value
        active_start = str(raw).strip() if raw else None
        if active_start:
            try:
                s = datetime.strptime(active_start, "%H:%M")
                active_hours = (now.hour * 60 + now.minute - (s.hour * 60 + s.minute)) / 60
            except ValueError:
                active_hours = 0.0

    total_so_far = completed_hours + active_hours
    remaining = TARGET_HOURS - total_so_far

    print()
    print("─" * 40)
    print(f"  📅  {today_str}  —  🕐 {now.strftime('%H:%M')}")
    print("─" * 40)

    # Completed sessions
    if completed_sessions:
        print(f"  Completed sessions ({len(completed_sessions)}):")
        for start, end in completed_sessions:
            print(f"    {start} → {end}")
    else:
        print("  No completed sessions yet.")

    # Active session
    if active_start:
        print(f"  Active session  : {active_start} → now  ({active_hours:.2f}h running)")
    else:
        print("  No active session.")

    print()
    print(f"  Logged so far   : {total_so_far:.2f}h  (target {TARGET_HOURS:.2f}h)")

    if remaining <= 0:
        over = -remaining
        print(f"  ✅  Target reached — {over:.2f}h over")
    else:
        if active_start:
            # Calculate leave time: how many more minutes needed from now
            leave_minutes = now.hour * 60 + now.minute + int(remaining * 60)
            leave_h, leave_m = divmod(leave_minutes, 60)
            print(f"  ⏳  Remaining       : {remaining:.2f}h")
            print(f"  🚪  Leave at        : {leave_h:02d}:{leave_m:02d}  (if session stays open)")
        else:
            print(f"  ⏳  Still needed    : {remaining:.2f}h  (no active session)")

    print("─" * 40)
    print()


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------
def _close_session(time_override=None):
    """Set End on the open session. Returns (wb, ws) or (None, None)."""
    if not os.path.exists(EXCEL_FILE):
        print("No timetracker file found. Run 'start' first.")
        return None, None

    wb = load_workbook(EXCEL_FILE)
    ws = wb[LOG_SHEET]

    open_row = find_open_session(ws)
    if not open_row:
        print("No open session found. Run 'start' first.")
        return None, None

    time_str = time_override or datetime.now().strftime("%H:%M")
    start_val = ws.cell(row=open_row, column=3).value
    date_val = ws.cell(row=open_row, column=1).value

    ws.cell(row=open_row, column=4, value=time_str)

    note = " (manually set)" if time_override else ""
    wb.save(EXCEL_FILE)
    print(f"⏸  Closed — {date_val}  {start_val} → {time_str}{note}")
    return wb, ws


def _print_day_summary(ws):
    today_str = date.today().strftime("%Y-%m-%d")
    days = read_log(ws)
    info = days.get(today_str)

    print()
    print("─" * 40)
    print(f"  📅  {today_str}")
    if not info:
        print("  No completed sessions today.")
    else:
        total = info["total"]
        diff = total - TARGET_HOURS
        is_over = diff >= 0
        symbol = "✅" if is_over else "⚠️ "
        sign = "+" if is_over else ""
        print(f"  Sessions : {len(info['sessions'])}")
        for start, end in info["sessions"]:
            print(f"    {start} → {end}")
        print(f"  Total    : {total:.2f}h  (target {TARGET_HOURS:.2f}h)")
        print(f"  Delta    : {symbol} {sign}{diff:.2f}h")
    print("─" * 40)
    print()
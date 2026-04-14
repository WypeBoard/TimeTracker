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
        print(f"⚠Session already running since {t}. Use 'pause' or 'stop' first.")
        return

    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = time_override or now.strftime("%H:%M")
    row = ws.max_row + 1

    ws.cell(row=row, column=1, value=date_str)
    ws.cell(row=row, column=2, value=f"=ISOWEEKNUM(A{row})")
    ws.cell(row=row, column=3, value=time_str)
    ws.cell(row=row, column=4, value=None)
    ws.cell(row=row, column=5,
            value=f'=IF(D{row}<>"",FLOOR((D{row}-C{row})*24,2),"")')
    format_log_row(ws, row)

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
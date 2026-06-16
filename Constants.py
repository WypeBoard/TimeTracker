import os

# Database file — stored under %APPDATA% per Windows convention.
DB_FILE = os.path.join(os.environ["APPDATA"], "TimeTracker", "timetracker.db")

TARGET_HOURS = 7.4
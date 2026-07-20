import sqlite3

from db.query_type import QueryType
from logger import get_logger

_log = get_logger(__name__)


class Connection:
    """Context manager that opens a SQLite connection, yields a cursor, then
    commits (WRITE) or skips commit (READ) and closes the connection on exit.

    Usage:
        with Connection(QueryType.WRITE, DB_FILE) as cur:
            cur.execute("INSERT INTO ...", params)
        # connection is committed and closed automatically

    If an exception occurs inside the block, the connection is closed without
    committing — SQLite rolls back the transaction automatically on close.

    __enter__ and __exit__ are Python special methods that implement the
    context manager protocol (the `with` statement). They are used here to
    guarantee the connection is always closed, even if an error occurs.
    """

    def __init__(self, query_type: QueryType, file: str):
        self.file = file
        self.query_type = query_type
        self._conn: sqlite3.Connection | None = None

    def __enter__(self) -> sqlite3.Cursor:
        try:
            self._conn = sqlite3.connect(self.file)
        except sqlite3.Error as exc:
            _log.error("Failed to connect to database %r: %s", self.file, exc)
            raise
        return self._conn.cursor()

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._conn:
            if self.query_type == QueryType.WRITE and exc_type is None:
                try:
                    self._conn.commit()
                except sqlite3.Error as exc:
                    _log.error("Failed to commit transaction: %s", exc)
                    raise
            self._conn.close()
        # Return None (falsy) so exceptions propagate normally.

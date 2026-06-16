from enum import Enum, auto


class QueryType(Enum):
    """Controls whether the database connection commits after a block exits.

    READ  — used for SELECT queries; no commit is performed.
    WRITE — used for INSERT, UPDATE, and DELETE; commits on successful exit.
    """
    READ  = auto()
    WRITE = auto()


import json
import sqlite3
import time
from contextlib import contextmanager

import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    text TEXT NOT NULL,
    sender TEXT,
    channel TEXT,
    metadata_json TEXT,
    received_at REAL
);

CREATE TABLE IF NOT EXISTS decisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id INTEGER NOT NULL,
    label TEXT NOT NULL,
    risk_score REAL NOT NULL,
    confidence REAL NOT NULL,
    reasons_json TEXT,
    evidence_json TEXT,
    action TEXT NOT NULL,
    created_at REAL,
    FOREIGN KEY(message_id) REFERENCES messages(id)
);

CREATE TABLE IF NOT EXISTS feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    decision_id INTEGER NOT NULL,
    feedback_type TEXT NOT NULL,  -- correct | false_positive | false_negative
    comment TEXT,
    created_at REAL,
    FOREIGN KEY(decision_id) REFERENCES decisions(id)
);

CREATE TABLE IF NOT EXISTS sender_profiles (
    sender TEXT PRIMARY KEY,
    message_count INTEGER DEFAULT 0,
    spam_count INTEGER DEFAULT 0,
    risk_score REAL DEFAULT 0.0,
    last_seen REAL
);

CREATE TABLE IF NOT EXISTS domain_profiles (
    domain TEXT PRIMARY KEY,
    seen_count INTEGER DEFAULT 0,
    spam_count INTEGER DEFAULT 0,
    risk_score REAL DEFAULT 0.0,
    last_checked REAL
);

CREATE TABLE IF NOT EXISTS thresholds (
    key TEXT PRIMARY KEY,
    value REAL NOT NULL
);
"""


@contextmanager
def get_conn():
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_conn() as conn:
        conn.executescript(SCHEMA)
        # seed default thresholds if empty
        existing = {r["key"] for r in conn.execute("SELECT key FROM thresholds")}
        for key, value in config.DEFAULT_THRESHOLDS.items():
            if key not in existing:
                conn.execute(
                    "INSERT INTO thresholds (key, value) VALUES (?, ?)", (key, value)
                )


def get_thresholds() -> dict:
    with get_conn() as conn:
        rows = conn.execute("SELECT key, value FROM thresholds").fetchall()
        if not rows:
            return dict(config.DEFAULT_THRESHOLDS)
        return {r["key"]: r["value"] for r in rows}


def set_threshold(key: str, value: float):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO thresholds (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, value),
        )


def save_message(text: str, sender: str, channel: str, metadata: dict) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO messages (text, sender, channel, metadata_json, received_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (text, sender, channel, json.dumps(metadata or {}), time.time()),
        )
        return cur.lastrowid


def save_decision(message_id: int, label: str, risk_score: float, confidence: float,
                   reasons: list, evidence: dict, action: str) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO decisions "
            "(message_id, label, risk_score, confidence, reasons_json, evidence_json, action, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (message_id, label, risk_score, confidence, json.dumps(reasons),
             json.dumps(evidence or {}), action, time.time()),
        )
        return cur.lastrowid


def save_feedback(decision_id: int, feedback_type: str, comment: str) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO feedback (decision_id, feedback_type, comment, created_at) "
            "VALUES (?, ?, ?, ?)",
            (decision_id, feedback_type, comment, time.time()),
        )
        return cur.lastrowid


def get_decision(decision_id: int):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM decisions WHERE id=?", (decision_id,)).fetchone()
        return dict(row) if row else None


def upsert_sender_profile(sender: str, is_spam: bool):
    if not sender:
        return
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM sender_profiles WHERE sender=?", (sender,)
        ).fetchone()
        if row is None:
            msg_count, spam_count = 1, (1 if is_spam else 0)
        else:
            msg_count = row["message_count"] + 1
            spam_count = row["spam_count"] + (1 if is_spam else 0)
        risk = spam_count / msg_count if msg_count else 0.0
        conn.execute(
            "INSERT INTO sender_profiles (sender, message_count, spam_count, risk_score, last_seen) "
            "VALUES (?, ?, ?, ?, ?) "
            "ON CONFLICT(sender) DO UPDATE SET message_count=excluded.message_count, "
            "spam_count=excluded.spam_count, risk_score=excluded.risk_score, last_seen=excluded.last_seen",
            (sender, msg_count, spam_count, risk, time.time()),
        )


def get_sender_profile(sender: str):
    if not sender:
        return None
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM sender_profiles WHERE sender=?", (sender,)
        ).fetchone()
        return dict(row) if row else None


def upsert_domain_profile(domain: str, is_spam: bool):
    if not domain:
        return
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM domain_profiles WHERE domain=?", (domain,)
        ).fetchone()
        if row is None:
            seen_count, spam_count = 1, (1 if is_spam else 0)
        else:
            seen_count = row["seen_count"] + 1
            spam_count = row["spam_count"] + (1 if is_spam else 0)
        risk = spam_count / seen_count if seen_count else 0.0
        conn.execute(
            "INSERT INTO domain_profiles (domain, seen_count, spam_count, risk_score, last_checked) "
            "VALUES (?, ?, ?, ?, ?) "
            "ON CONFLICT(domain) DO UPDATE SET seen_count=excluded.seen_count, "
            "spam_count=excluded.spam_count, risk_score=excluded.risk_score, last_checked=excluded.last_checked",
            (domain, seen_count, spam_count, risk, time.time()),
        )


def get_domain_profile(domain: str):
    if not domain:
        return None
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM domain_profiles WHERE domain=?", (domain,)
        ).fetchone()
        return dict(row) if row else None


def all_sender_profiles():
    with get_conn() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT * FROM sender_profiles ORDER BY risk_score DESC"
        )]


def all_domain_profiles():
    with get_conn() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT * FROM domain_profiles ORDER BY risk_score DESC"
        )]


def recent_decisions(limit=20):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT d.*, m.text as message_text, m.sender as sender "
            "FROM decisions d JOIN messages m ON d.message_id = m.id "
            "ORDER BY d.id DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]


def feedback_stats():
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT feedback_type, COUNT(*) as n FROM feedback GROUP BY feedback_type"
        ).fetchall()
        return {r["feedback_type"]: r["n"] for r in rows}

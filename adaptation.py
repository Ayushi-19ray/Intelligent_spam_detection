
import json

import db


STEP = 0.01
BOUNDS = {
    "block_at": (0.65, 0.95),
    "quarantine_at": (0.45, 0.80),
    "warn_at": (0.15, 0.55),
}


def _clamp(key, value):
    lo, hi = BOUNDS.get(key, (0.0, 1.0))
    return max(lo, min(hi, value))


def record_feedback(decision_id: int, feedback_type: str, comment: str = "") -> dict:
    
    assert feedback_type in ("correct", "false_positive", "false_negative")

    decision = db.get_decision(decision_id)
    if decision is None:
        raise ValueError(f"No decision with id {decision_id}")

    db.save_feedback(decision_id, feedback_type, comment)

    
    with db.get_conn() as conn:
        msg_row = conn.execute(
            "SELECT * FROM messages WHERE id=?", (decision["message_id"],)
        ).fetchone()
    sender = msg_row["sender"] if msg_row else None

    thresholds = db.get_thresholds()

    if feedback_type == "false_positive":
        
        for key in ("block_at", "quarantine_at", "warn_at"):
            new_val = _clamp(key, thresholds[key] + STEP)
            db.set_threshold(key, new_val)
        
        if sender:
            db.upsert_sender_profile(sender, is_spam=False)

    elif feedback_type == "false_negative":
        
        for key in ("block_at", "quarantine_at", "warn_at"):
            new_val = _clamp(key, thresholds[key] - STEP)
            db.set_threshold(key, new_val)
        if sender:
            db.upsert_sender_profile(sender, is_spam=True)

    

    return {
        "decision_id": decision_id,
        "feedback_type": feedback_type,
        "updated_thresholds": db.get_thresholds(),
    }

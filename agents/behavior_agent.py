import re
import time

import db

FREE_EMAIL_LOOKALIKE_TLDS = {".xyz", ".top", ".click", ".info", ".buzz"}


def analyze(sender: str, channel: str, metadata: dict) -> dict:
    metadata = metadata or {}
    reasons = []
    score = 0.0

    
    profile = db.get_sender_profile(sender) if sender else None
    if profile and profile["message_count"] >= 2:
        if profile["risk_score"] >= 0.6:
            score += 0.35
            reasons.append(
                f"Sender has a history of spam flags in memory "
                f"({profile['spam_count']}/{profile['message_count']} past messages)"
            )
        elif profile["risk_score"] <= 0.05:
            score -= 0.10  
            reasons.append("Sender has a clean history in memory")

    
    if sender and "@" in sender:
        local, _, domain = sender.partition("@")
        if re.search(r"\d{4,}", local):
            score += 0.10
            reasons.append(f"Sender local-part contains a long random-looking number ({local})")
        if domain and ("." + domain.rsplit(".", 1)[-1]) in FREE_EMAIL_LOOKALIKE_TLDS:
            score += 0.15
            reasons.append(f"Sender domain uses a high-abuse TLD ({domain})")

    
    account_age_days = metadata.get("account_age_days")
    if isinstance(account_age_days, (int, float)) and account_age_days < 3:
        score += 0.20
        reasons.append(f"Sending account is brand new ({account_age_days} days old)")

    send_rate_per_hour = metadata.get("send_rate_per_hour")
    if isinstance(send_rate_per_hour, (int, float)) and send_rate_per_hour > 50:
        score += 0.25
        reasons.append(f"Abnormally high send rate ({send_rate_per_hour}/hr) suggests bulk/bot sending")

    reply_to = metadata.get("reply_to")
    if reply_to and sender and "@" in sender and "@" in reply_to:
        sender_domain = sender.split("@")[-1]
        reply_domain = reply_to.split("@")[-1]
        if sender_domain != reply_domain:
            score += 0.15
            reasons.append(f"Reply-To domain ({reply_domain}) differs from sender domain ({sender_domain})")

    hour = metadata.get("send_hour_local")
    if isinstance(hour, int) and (hour < 5 or hour > 23):
        score += 0.05
        reasons.append(f"Sent at unusual local hour ({hour}:00)")

    score = max(0.0, min(1.0, score))
    return {"score": score, "reasons": reasons}

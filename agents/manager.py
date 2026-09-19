
import db
from agents import content_agent, link_agent, behavior_agent, evidence_agent, critic_agent, reporter_agent


def analyze_message(text: str, sender: str = None, channel: str = "email",
                     metadata: dict = None) -> dict:
    
    db.init_db()
    metadata = metadata or {}

    
    message_id = db.save_message(text, sender, channel, metadata)

    
    content_result = content_agent.analyze(text)
    link_result = link_agent.analyze(text)
    behavior_result = behavior_agent.analyze(sender, channel, metadata)

    
    thresholds = db.get_thresholds()
    prelim_score = (
        content_result["score"] * 0.4 + link_result["score"] * 0.35 + behavior_result["score"] * 0.25
    )
    evidence_result = None
    link_is_suspicious = link_result["score"] >= 0.2  # shortener/IP/lookalike already flagged something
    prelim_in_band = thresholds["evidence_trigger_low"] <= prelim_score <= thresholds["evidence_trigger_high"]
    
    if prelim_in_band or link_is_suspicious:
        evidence_result = evidence_agent.gather(text, link_result.get("domains", []))

    
    critic_result = critic_agent.review(content_result, link_result, behavior_result, evidence_result)

    
    is_spam = critic_result["label"] in ("spam", "suspicious")
    action = reporter_agent.recommend_action(critic_result["risk_score"])

    decision_id = db.save_decision(
        message_id=message_id,
        label=critic_result["label"],
        risk_score=critic_result["risk_score"],
        confidence=critic_result["confidence"],
        reasons=critic_result["top_reasons"],
        evidence=evidence_result or {},
        action=action,
    )

    
    db.upsert_sender_profile(sender, is_spam)
    for domain in link_result.get("domains", []):
        db.upsert_domain_profile(domain, is_spam)

    report = reporter_agent.build_report(
        message_id=message_id,
        decision_id=decision_id,
        text=text,
        sender=sender,
        channel=channel,
        critic_result=critic_result,
        link_domains=link_result.get("domains", []),
        evidence=evidence_result,
    )
    return report

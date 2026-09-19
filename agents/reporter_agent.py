
import db


def recommend_action(risk_score: float) -> str:
    t = db.get_thresholds()
    if risk_score >= t["block_at"]:
        return "block"
    if risk_score >= t["quarantine_at"]:
        return "quarantine"
    if risk_score >= t["warn_at"]:
        return "warn"
    return "allow"


def build_report(message_id: int, decision_id: int, text: str, sender: str,
                  channel: str, critic_result: dict, link_domains: list,
                  evidence: dict | None) -> dict:
    action = recommend_action(critic_result["risk_score"])
    return {
        "decision_id": decision_id,
        "message_id": message_id,
        "channel": channel,
        "sender": sender,
        "message_preview": (text[:140] + "…") if len(text) > 140 else text,
        "label": critic_result["label"],
        "risk_score": critic_result["risk_score"],
        "confidence": critic_result["confidence"],
        "recommended_action": action,
        "top_reasons": critic_result["top_reasons"],
        "agent_scores": critic_result["agent_scores"],
        "agent_agreement_spread": critic_result["agent_agreement_spread"],
        "links_found": link_domains,
        "evidence": evidence if evidence and evidence.get("available") else None,
    }


def pretty_print(report: dict) -> str:
    lines = [
        "=" * 60,
        f"  SPAM DETECTION REPORT  (decision #{report['decision_id']})",
        "=" * 60,
        f"Sender     : {report['sender'] or 'unknown'}",
        f"Channel    : {report['channel']}",
        f"Message    : {report['message_preview']!r}",
        "-" * 60,
        f"LABEL      : {report['label'].upper()}",
        f"Risk score : {report['risk_score']:.2f}  (confidence {report['confidence']:.2f})",
        f"ACTION     : {report['recommended_action'].upper()}",
        "-" * 60,
        "Top reasons:",
    ]
    if report["top_reasons"]:
        for r in report["top_reasons"]:
            lines.append(f"  • {r}")
    else:
        lines.append("  • No strong risk signals found")
    lines.append("-" * 60)
    lines.append(
        f"Agent scores -> content: {report['agent_scores']['content']:.2f}  "
        f"link: {report['agent_scores']['link']:.2f}  "
        f"behavior: {report['agent_scores']['behavior']:.2f}  "
        f"evidence: {report['agent_scores']['evidence']:.2f}"
    )
    if report["links_found"]:
        lines.append(f"Links/domains found: {', '.join(report['links_found'])}")
    if report["evidence"]:
        lines.append(f"Extra evidence: {report['evidence'].get('reasons')}")
    lines.append("=" * 60)
    return "\n".join(lines)

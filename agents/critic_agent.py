
import config
import db


def _consistency_check(content, link, behavior):
    
    scores = [content["score"], link["score"], behavior["score"]]
    spread = max(scores) - min(scores)
    return spread


def review(content: dict, link: dict, behavior: dict, evidence: dict | None) -> dict:
    weights = config.AGENT_WEIGHTS

    weighted_sum = content["score"] * weights["content"]
    weight_used = weights["content"]

    
    if link.get("domains"):
        weighted_sum += link["score"] * weights["link"]
        weight_used += weights["link"]

    weighted_sum += behavior["score"] * weights["behavior"]
    weight_used += weights["behavior"]

    if evidence and evidence.get("available"):
        weighted_sum += evidence.get("score_delta", 0.0) * weights["evidence"] / 0.1
        weight_used += weights["evidence"]  
    
    

    risk_score = round(weighted_sum / weight_used if weight_used else 0.0, 3)
    risk_score = max(0.0, min(1.0, risk_score))

    spread = _consistency_check(content, link, behavior)
    
    base_confidence = 0.95 - (spread * 0.5)
    
    signal_count = sum(1 for r in [content["reasons"], link["reasons"], behavior["reasons"]] if r)
    if signal_count == 0:
        base_confidence -= 0.15
    confidence = round(max(0.3, min(0.98, base_confidence)), 3)

    thresholds = db.get_thresholds()
    if risk_score >= thresholds["quarantine_at"]:
        label = "spam"
    elif risk_score >= thresholds["warn_at"]:
        label = "suspicious"
    else:
        label = "ham"

    all_reasons = []
    all_reasons.extend(content["reasons"])
    all_reasons.extend(link["reasons"])
    all_reasons.extend(behavior["reasons"])
    if evidence:
        all_reasons.extend(evidence.get("reasons", []))

    
    seen = set()
    top_reasons = []
    for r in all_reasons:
        if r not in seen:
            seen.add(r)
            top_reasons.append(r)
    top_reasons = top_reasons[:6]

    return {
        "risk_score": risk_score,
        "confidence": confidence,
        "label": label,
        "top_reasons": top_reasons,
        "agent_scores": {
            "content": content["score"],
            "link": link["score"],
            "behavior": behavior["score"],
            "evidence": (evidence.get("score_delta") if evidence else 0.0) or 0.0,
        },
        "agent_agreement_spread": round(spread, 3),
    }

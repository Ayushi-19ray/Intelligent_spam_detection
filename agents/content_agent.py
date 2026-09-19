
import json
import re

import config

URGENCY_WORDS = [
    "urgent", "immediately", "act now", "verify your account", "suspended",
    "limited time", "expires today", "final notice", "act fast", "hurry",
    "respond immediately", "within 24 hours", "account will be closed",
]

MONEY_HOOK_WORDS = [
    "free", "winner", "won", "cash prize", "lottery", "claim your", "reward",
    "100% free", "guaranteed", "no cost", "risk free", "$$$", "million dollars",
    "inheritance", "congratulations you", "click to claim",
]

PHISHING_PHRASES = [
    "confirm your password", "update your billing", "verify your identity",
    "unusual login activity", "your account has been locked",
    "click here to verify", "re-enter your credit card", "ssn", "social security number",
    "one time password", "otp is", "bank details", "wire transfer",
]

IMPERSONATION_PHRASES = [
    "changed my number", "new number", "lost my phone", "phone is broken",
    "phone broke", "message me here", "save this number", "this is my new number",
]

SUSPICIOUS_PUNCT = re.compile(r"[!?]{2,}")
ALL_CAPS_WORD = re.compile(r"\b[A-Z]{4,}\b")
EXCESSIVE_EMOJI = re.compile(
    r"[\U0001F300-\U0001FAFF\U00002700-\U000027BF]{3,}"
)


def _heuristic_score(text: str):
    reasons = []
    t = text.lower()
    score = 0.0

    hits = [w for w in URGENCY_WORDS if w in t]
    if hits:
        score += min(0.30, 0.12 * len(hits))
        reasons.append(f"Urgency/pressure language detected ({', '.join(hits[:3])})")

    hits = [w for w in MONEY_HOOK_WORDS if w in t]
    if hits:
        score += min(0.35, 0.12 * len(hits))
        reasons.append(f"Unsolicited reward/money hook ({', '.join(hits[:3])})")

    hits = [w for w in PHISHING_PHRASES if w in t]
    if hits:
        score += min(0.40, 0.15 * len(hits))
        reasons.append(f"Credential/financial-data phishing pattern ({', '.join(hits[:3])})")

    hits = [w for w in IMPERSONATION_PHRASES if w in t]
    if hits:
        score += min(0.55, 0.25 * len(hits))
        reasons.append(f"Possible impersonation/number-change scam pattern ({', '.join(hits[:3])})")

    if SUSPICIOUS_PUNCT.search(text):
        score += 0.05
        reasons.append("Excessive punctuation (!!, ??)")

    caps_hits = ALL_CAPS_WORD.findall(text)
    if len(caps_hits) >= 2:
        score += 0.08
        reasons.append(f"Excessive ALL-CAPS shouting ({len(caps_hits)} words)")

    if EXCESSIVE_EMOJI.search(text):
        score += 0.05
        reasons.append("Excessive emoji clustering")

    if len(text) < 15 and re.search(r"https?://", t):
        score += 0.1
        reasons.append("Very short message dominated by a link")

    score = max(0.0, min(1.0, score))
    return score, reasons


def _llm_score(text: str):
    """Optional upgrade: ask an LLM for a nuanced spam score + reasons.
    Uses OpenAI if OPENAI_API_KEY is set, else falls back to Groq (free,
    no credit card, OpenAI-compatible endpoint) if GROQ_API_KEY is set.
    Fails soft on any error."""
    if not config.HAS_LLM:
        return None
    try:
        from openai import OpenAI
        if config.HAS_OPENAI:
            client = OpenAI(api_key=config.OPENAI_API_KEY)
            model = config.OPENAI_MODEL
        else:
            client = OpenAI(api_key=config.GROQ_API_KEY, base_url=config.GROQ_BASE_URL)
            model = config.GROQ_MODEL
        prompt = (
            "You are a spam/phishing content classifier. Given the message below, "
            "return ONLY a JSON object with keys: "
            '"score" (float 0.0-1.0, likelihood this is spam/phishing/scam), '
            '"reasons" (list of up to 4 short strings explaining why). '
            "No preamble, no markdown fences.\n\n"
            f"MESSAGE:\n{text}"
        )
        resp = client.chat.completions.create(
            model=model,
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = resp.choices[0].message.content.strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        data = json.loads(raw)
        score = float(data.get("score", 0.0))
        reasons = [f"LLM: {r}" for r in data.get("reasons", [])]
        return max(0.0, min(1.0, score)), reasons
    except Exception:
        return None


def analyze(text: str) -> dict:
    """Returns {"score": float, "reasons": [str], "mode": "heuristic"|"heuristic+llm"}"""
    h_score, h_reasons = _heuristic_score(text)
    llm_result = _llm_score(text)

    if llm_result is None:
        return {"score": h_score, "reasons": h_reasons, "mode": "heuristic"}

    llm_score, llm_reasons = llm_result
    
    blended = round(0.65 * llm_score + 0.35 * h_score, 3)
    return {
        "score": blended,
        "reasons": h_reasons + llm_reasons,
        "mode": "heuristic+llm",
    }
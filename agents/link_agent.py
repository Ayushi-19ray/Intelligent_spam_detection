
import re
from urllib.parse import urlparse

import config
import db

URL_RE = re.compile(r"https?://[^\s<>\)\]\"']+", re.IGNORECASE)

URL_SHORTENERS = {
    "bit.ly", "tinyurl.com", "t.co", "goo.gl", "ow.ly", "is.gd", "buff.ly",
    "cutt.ly", "rb.gy", "shorturl.at",
}

SUSPICIOUS_TLDS = {
    ".tk", ".ml", ".ga", ".cf", ".gq", ".xyz", ".top", ".club", ".work",
    ".info", ".click", ".link", ".zip", ".rest",
}

WELL_KNOWN_BRANDS = [
    "paypal", "amazon", "apple", "microsoft", "google", "netflix", "bankofamerica",
    "chase", "wellsfargo", "facebook", "instagram", "irs", "hdfcbank", "icicibank",
    "sbi", "axisbank",
]


def _levenshtein(a: str, b: str) -> int:
    if a == b:
        return 0
    if len(a) == 0:
        return len(b)
    if len(b) == 0:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i] + [0] * len(b)
        for j, cb in enumerate(b, 1):
            cost = 0 if ca == cb else 1
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + cost)
        prev = cur
    return prev[-1]


def extract_urls(text: str):
    return URL_RE.findall(text)


def _domain_of(url: str) -> str:
    try:
        netloc = urlparse(url).netloc.lower()
        return netloc.split("@")[-1].split(":")[0]
    except Exception:
        return ""


def _is_ip_literal(domain: str) -> bool:
    return bool(re.match(r"^\d{1,3}(\.\d{1,3}){3}$", domain))


def _lookalike_brand(domain: str):
    core = domain.split(".")[0]
    
    parts = re.split(r"[-_.]", core)
    candidates = [core] + parts
    for candidate in candidates:
        if len(candidate) < 4:
            continue
        for brand in WELL_KNOWN_BRANDS:
            if candidate == brand:
                continue
            dist = _levenshtein(candidate, brand)
            if 0 < dist <= 2:
                return brand
    return None


def _tavily_reputation_check(domain: str):
    if not config.HAS_TAVILY:
        return None
    try:
        from tavily import TavilyClient
        client = TavilyClient(api_key=config.TAVILY_API_KEY)
        result = client.search(query=f"{domain} scam OR phishing OR fraud reports", max_results=3)
        snippets = [r.get("content", "")[:200] for r in result.get("results", [])]
        flagged = any(
            kw in " ".join(snippets).lower()
            for kw in ["scam", "phishing", "fraud", "malware", "blacklist"]
        )
        return {"domain": domain, "flagged": flagged, "snippets": snippets}
    except Exception:
        return None


def analyze(text: str) -> dict:
    urls = extract_urls(text)
    if not urls:
        return {"score": 0.0, "reasons": [], "domains": [], "evidence": None}

    reasons = []
    score = 0.0
    domains = []
    evidence = None

    for url in urls:
        domain = _domain_of(url)
        if not domain:
            continue
        domains.append(domain)

        if domain in URL_SHORTENERS:
            score += 0.30
            reasons.append(f"Uses URL shortener that hides real destination ({domain})")

        tld = "." + domain.rsplit(".", 1)[-1] if "." in domain else ""
        if tld in SUSPICIOUS_TLDS:
            score += 0.25
            reasons.append(f"Suspicious/high-abuse TLD ({tld})")

        if _is_ip_literal(domain):
            score += 0.40
            reasons.append(f"Raw IP-address link instead of a domain ({domain})")

        lookalike = _lookalike_brand(domain)
        if lookalike:
            score += 0.35
            reasons.append(f"Domain looks like a lookalike of '{lookalike}' ({domain})")

        profile = db.get_domain_profile(domain)
        if profile and profile["seen_count"] >= 3 and profile["risk_score"] >= 0.5:
            score += 0.25
            reasons.append(
                f"Domain has prior spam history in memory "
                f"({profile['spam_count']}/{profile['seen_count']} past flags)"
            )

    # Only spend a web-search call on the first genuinely suspicious domain
    if score > 0 and domains:
        evidence = _tavily_reputation_check(domains[0])
        if evidence and evidence.get("flagged"):
            score += 0.25
            reasons.append(f"Web search found scam/phishing reports for {domains[0]}")

    score = max(0.0, min(1.0, score))
    return {"score": score, "reasons": reasons, "domains": list(set(domains)), "evidence": evidence}


import config


def gather(text: str, domains: list) -> dict:
    if not config.HAS_TAVILY:
        return {"available": False, "score_delta": 0.0, "reasons": []}

    try:
        from tavily import TavilyClient
        client = TavilyClient(api_key=config.TAVILY_API_KEY)

        
        excerpt = text.strip()[:120]
        query = f'"{excerpt}" scam report'
        result = client.search(query=query, max_results=3)
        hits = result.get("results", [])

        reasons = []
        score_delta = 0.0
        if hits:
            score_delta += 0.15
            reasons.append(
                f"Web search found {len(hits)} report(s) matching this message's wording/pattern"
            )

        return {
            "available": True,
            "score_delta": min(0.3, score_delta),
            "reasons": reasons,
            "sources": [h.get("url") for h in hits],
        }
    except Exception:
        
        return {"available": False, "score_delta": 0.0, "reasons": []}


import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    
    pass

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
GROQ_BASE_URL = "https://api.groq.com/openai/v1"

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "").strip()

HAS_OPENAI = bool(OPENAI_API_KEY)
HAS_GROQ = bool(GROQ_API_KEY)
HAS_LLM = HAS_OPENAI or HAS_GROQ
HAS_TAVILY = bool(TAVILY_API_KEY)


DB_PATH = os.getenv("SPAM_AGENT_DB", "spam_agent.db")


DEFAULT_THRESHOLDS = {
    "block_at": 0.78,       
    "quarantine_at": 0.58,  
    "warn_at": 0.35,        
    
    "evidence_trigger_low": 0.35,   
    "evidence_trigger_high": 0.65,
}


AGENT_WEIGHTS = {
    "content": 0.40,
    "link": 0.30,
    "behavior": 0.20,
    "evidence": 0.10,
}

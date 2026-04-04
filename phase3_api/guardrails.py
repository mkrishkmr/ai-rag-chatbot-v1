import re
import logging

logger = logging.getLogger("groww.guardrails")

SYSTEM_PROMPT = """You are the Groww AI Fact Engine. 

### SCOPE
You ONLY have knowledge about these 4 funds:
1. Groww Nifty 50 Index Fund
2. Groww Value Fund
3. Groww Aggressive Hybrid Fund
4. Groww ELSS Tax Saver Fund

If asked about ANY other fund, or general advice, you must state you only have data for these 4.

### RULES
1. NO MARKDOWN: Never use symbols like "**", "###", "__", or "#". Use plain sentences only.
2. BREVITY: Maximum 3 short sentences.
3. NO ADVICE: Never suggest, recommend, or compare. Facts only.
4. SOURCE TAGS: You MUST use the structural tags [ANSWER], [SOURCE_SUMMARIES], and [NEXT_STEPS].

[ANSWER]
(Factual answer here. Use plain sentences. No bolding. No symbols.)
[/ANSWER]

[SOURCE_SUMMARIES]
- (1 sentence summary)
[/SOURCE_SUMMARIES]

[NEXT_STEPS]
- (1 follow-up question)
[/NEXT_STEPS]

---
REAL-TIME GROUND TRUTH:
{live_metrics}

---
CONTEXT CHUNKS:
{context}
---
LAST UPDATED: 05 Apr 2026"""

def get_system_prompt(context: str, live_metrics: str = "No live metrics available.") -> str:
    """Returns the formatted system prompt with the given context and live metrics."""
    return SYSTEM_PROMPT.format(context=context, live_metrics=live_metrics, question="")

def detect_pii(text: str) -> bool:
    """Returns True if a PAN or Aadhaar pattern is detected in the string."""
    pan_pattern = r'\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b'
    aadhaar_pattern = r'\b\d{4}\s?\d{4}\s?\d{4}\b'
    
    if re.search(pan_pattern, text, re.IGNORECASE) or re.search(aadhaar_pattern, text):
        return True
    return False

# Keywords that indicate the query is about the 4 funds in scope.
# A query must match at least 1 keyword to pass the scope gate.
# Add terms here as the knowledge base grows — do not make this list
# smaller or the gate will become too aggressive.
_SCOPE_KEYWORDS = [
    # Fund identifiers
    "nifty 50", "nifty50", "index fund",
    "value fund",
    "aggressive hybrid", "hybrid fund",
    "elss", "tax saver",
    "groww",
    "nikhil satam", "aakash chauhan", "shashi kumar",
    "nav", "net asset value", "aum", "expense ratio",
    "exit load", "sip", "fund manager", "returns",
    "exit",
    "finds",
    "fund",
    "funds",
    "scheme",
    "invest",
    "information",
    "info",
    "data",
    "tell me",
    "what do you know",
    "what can you",
    "redeem",
    "withdraw",
    "lock",
    "when can",
    "how long",
    "maturity",
    "statement",
    "capital gains",
    "download",
    "how do i"
]

def is_query_in_scope(query: str) -> bool:
    """
    Returns True if the query is about one of the 4 Groww funds, or a general question about the chatbot's knowledge.
    """
    META_PATTERNS = [
        "what do you know",
        "what can you",
        "what all",
        "what info",
        "what information",
        "tell me about",
        "what data",
        "what have you",
        "summarize",
        "summary",
        "overview",
    ]
    q_lower = query.lower()
    if any(p in q_lower for p in META_PATTERNS):
        return True

    q = query.lower()
    
    exclusions = ["sbi", "hdfc", "mirae", "cricket", "weather", "python"]
    if any(ex in q for ex in exclusions):
        return False
        
    return any(keyword in q for keyword in _SCOPE_KEYWORDS)

# Alias for test compatibility
contains_pii = detect_pii

ADVICE_PATTERNS = [
    "can i invest",
    "should i invest",
    "is it good to invest",
    "worth investing",
    "recommend",
    "which fund should",
    "better fund",
    "best fund",
    "better",
    "best",
    "good",
    "should i buy",
    "should i sell",
    "should i redeem",
    "good investment",
    "is it worth",
    "will it grow",
    "will i get returns",
    "predict",
    "forecast",
    "should i buy this",
    "should i invest in this",
    "is this worth it",
    "is this good",
    "better for me",
    "best for me",
    "buy this",
    "sell this",
    "invest in this",
    "worth it to buy",
]

def is_advice_query(query: str) -> bool:
    """
    Returns True if the query is asking for investment advice
    rather than factual information. These must be blocked
    before reaching the LLM regardless of scope.
    """
    q = query.lower()
    return any(p in q for p in ADVICE_PATTERNS)

import re

def detect_pii(text: str) -> bool:
    """Returns True if a PAN or Aadhaar pattern is detected in the string."""
    pan_pattern = r'[A-Z]{5}[0-9]{4}[A-Z]{1}'
    aadhaar_pattern = r'\b\d{12}\b'
    
    if re.search(pan_pattern, text, re.IGNORECASE) or re.search(aadhaar_pattern, text):
        return True
    return False

def get_system_prompt(hybrid_context: str) -> str:
    """Returns the strict system prompt for the Facts-Only Chatbot."""
    return f"""
    You are a factual mutual fund assistant for official Groww Mutual Fund schemes.
    
    RULES:
    1. Answer concisely but use excellent grammar and professional formatting.
    2. Always cite the Source URL from the context at the very end of your response.
    3. If the user asks for investment advice, predictions, or "which fund is better", you MUST refuse and reply: "I provide official facts only. Consult a SEBI-registered advisor."
    4. Only use the provided context to answer. If you don't know, say so.
    5. If answering for multiple funds, format your answer as a clean Markdown bulleted list.
    
    CONTEXT:
    {hybrid_context}
    """

import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage

load_dotenv()

# Simulate the context retrieval for a Nifty 50 query
context = """
[Web] Groww Nifty 50 Index Fund Direct Growth
NAV: 9.06 (14 Mar 2026)
Expense Ratio: 0.15% (Direct)
Exit Load: Nil
"""

system_prompt = f"""You are the Groww AI Fact Engine.
You MUST respond using [ANSWER] tags.
BREVITY: Keep it to 2 sentences.
LAST UPDATED FOOTER: Use 'Last updated from sources: 14 Mar 2026'

### CONTEXT:
{context}
"""

human_query = "What is the expense ratio for Nifty 50?"

chat = ChatGoogleGenerativeAI(model="gemini-3.1-pro-preview", temperature=0)
response = chat.invoke([SystemMessage(content=system_prompt), HumanMessage(content=human_query)])

print("--- RAW LLM RESPONSE ---")
print(response.content)
print("--- END ---")

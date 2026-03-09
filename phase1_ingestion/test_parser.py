import re
from bs4 import BeautifulSoup

def clean_text(element):
    if not element:
        return None
    text = element.get_text(separator=' ', strip=True)
    text = ' '.join(text.split())
    return text

with open("dump.html", "r", encoding="utf-8") as f:
    soup = BeautifulSoup(f, "html.parser")

def extract_from_table_or_div(keyword_regex):
    matches = soup.find_all(string=re.compile(keyword_regex, re.IGNORECASE))
    results = []
    for elem in matches:
        if elem.parent.name in ['script', 'style']: continue
        parent = elem.find_parent()
        if not parent: continue
        
        # 1. Next sibling
        next_sibling = parent.find_next_sibling()
        if next_sibling:
            text = clean_text(next_sibling)
            if text:
                results.append(text)
                continue
            
        # 2. Grandparent next sibling
        grandparent = parent.find_parent()
        if grandparent:
            next_gp_sibling = grandparent.find_next_sibling()
            if next_gp_sibling:
                text = clean_text(next_gp_sibling)
                if text:
                    results.append(text)
                    continue

    for res in results:
        # Avoid dictionary definition popup text
        if "fee payable" not in res.lower() and "percentage of your capital" not in res.lower():
            return res
            
    return results[-1] if results else "Not Found"

print("NAV:", extract_from_table_or_div(r"^NAV"))
print("Expense Ratio:", extract_from_table_or_div(r"^Expense ratio"))
print("Exit Load:", extract_from_table_or_div(r"^Exit load"))
print("Fund Size:", extract_from_table_or_div(r"^Fund size"))
print("Benchmark:", extract_from_table_or_div(r"Fund benchmark"))
print("Min. SIP:", extract_from_table_or_div(r"Min\. for SIP"))
print("Min. Lumpsum:", extract_from_table_or_div(r"Min\. for 1st investment"))

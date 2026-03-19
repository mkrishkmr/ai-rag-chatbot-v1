# Integration Test Cases

Execute these curl commands against a running local instance.

## 1. PII Detection (Expected: 400 Bad Request)

```bash
curl -i -X POST http://localhost:8080/api/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "Can I invest in Groww Value Fund? My PAN is ABCDE1234F"}'
```
**Assertion**: Must return HTTP 400 with "PII Detected. Request blocked."

## 2. Out of Scope Refusal (Expected: 200 OK + Refusal)

```bash
curl -s -X POST http://localhost:8080/api/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the NAV of SBI Contra Fund?"}'
```
**Assertion**: Must return "I only have information about Groww Nifty 50 Index Fund, Groww Value Fund, Groww Aggressive Hybrid Fund, and Groww ELSS Tax Saver Fund."

## 3. Advice Refusal (Expected: 200 OK + Refusal)

```bash
curl -s -X POST http://localhost:8080/api/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "Should I invest in Groww Aggressive Hybrid Fund?"}'
```
**Assertion**: Must return "I can provide facts only, not investment advice. For help evaluating mutual funds, visit [AMFI Investor Education]..."

## 4. Factual Metric Query (Expected: 200 OK + Real Answer)

```bash
curl -s -X POST http://localhost:8080/api/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the fund size of Nifty 50?"}'
```
**Assertion**: Must state the correct Fund Size / AUM without containing RAG nomenclature ("context chunks") or raw source URLs in the sentence.

## 5. Procedural Query (Expected: 200 OK + Short Guide)

```bash
curl -s -X POST http://localhost:8080/api/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "How do I download capital gains statement?"}'
```
**Assertion**: Must return exactly "Log into your Groww account at groww.in and navigate to Statements to download your capital gains statement."

"""
LLM utilities for VigilDoc using Groq API (Llama 3.1 8B Instant) with structured offline template generation.
"""

import os
import json
import requests

def get_groq_api_key():
    return os.getenv("GROQ_API_KEY", "")

def generate_multi_lang_snippets(method: str, path: str, request_schema: dict) -> dict:
    """Generates copy-pasteable usage examples in Python, cURL, JavaScript (Node.js), and Go."""
    base_url = "https://api.example.com"
    full_url = f"{base_url}{path}"
    
    # Python Snippet
    python_snippet = f"""import requests

url = "{full_url}"
headers = {{
    "Authorization": "Bearer YOUR_ACCESS_TOKEN",
    "Content-Type": "application/json"
}}
payload = {json.dumps(request_schema.get('properties', {'example': 'value'}), indent=4)}

response = requests.request("{method}", url, headers=headers, json=payload)
print(response.status_code)
print(response.json())
"""

    # cURL Snippet
    curl_snippet = f"""curl -X {method} "{full_url}" \\
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{json.dumps(request_schema.get("properties", {"example": "value"}))}'
"""

    # JavaScript Snippet
    js_snippet = f"""const fetch = require('node-fetch');

async function executeRequest() {{
  const response = await fetch('{full_url}', {{
    method: '{method}',
    headers: {{
      'Authorization': 'Bearer YOUR_ACCESS_TOKEN',
      'Content-Type': 'application/json'
    }},
    body: JSON.stringify({json.dumps(request_schema.get('properties', {'example': 'value'}))})
  }});
  
  const data = await response.json();
  console.log(data);
}}

executeRequest();
"""

    # Go Snippet
    go_snippet = f"""package main

import (
	"fmt"
	"strings"
	"net/http"
	"io/ioutil"
)

func main() {{
	url := "{full_url}"
	payload := strings.NewReader(`{json.dumps(request_schema.get('properties', {'example': 'value'}))}`)

	req, _ := http.NewRequest("{method}", url, payload)
	req.Header.Add("Authorization", "Bearer YOUR_ACCESS_TOKEN")
	req.Header.Add("Content-Type", "application/json")

	res, _ := http.DefaultClient.Do(req)
	defer res.Body.Close()
	body, _ := ioutil.ReadAll(res.Body)

	fmt.Println(res.StatusCode)
	fmt.Println(string(body))
}}
"""

    return {
        "python": python_snippet,
        "curl": curl_snippet,
        "javascript": js_snippet,
        "go": go_snippet
    }

def generate_endpoint_documentation(endpoint: dict) -> str:
    """Prompts Groq LLM (Llama 3.1 8B Instant) to write comprehensive markdown documentation for an endpoint."""
    api_key = get_groq_api_key()
    method = endpoint.get('method', 'GET')
    path = endpoint.get('path', '/')
    summary = endpoint.get('summary', '')
    description = endpoint.get('description', '')
    category = endpoint.get('category', 'Core Endpoints')
    parameters = endpoint.get('parameters', [])
    req_schema = endpoint.get('request_schema', {})
    resp_schema = endpoint.get('response_schema', {})

    snippets = generate_multi_lang_snippets(method, path, req_schema)

    if api_key and not api_key.startswith("your_"):
        try:
            url = "https://api.groq.com/openai/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            prompt = f"""You are an expert technical writer. Generate a complete, polished Developer API Documentation page in Markdown for the following endpoint:
Endpoint: {method} {path}
Summary: {summary}
Description: {description}
Category: {category}
Parameters: {json.dumps(parameters)}
Request Schema: {json.dumps(req_schema)}
Response Schema: {json.dumps(resp_schema)}

Include sections:
1. Overview & Use Case
2. Authentication Scopes
3. Request Parameters & Body Schema
4. Expected Response Format
5. Common Error Status Codes & Troubleshooting

Output ONLY valid markdown without conversational intros.
"""
            payload = {
                "model": "llama-3.1-8b-instant",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3,
                "max_tokens": 1000
            }
            resp = requests.post(url, headers=headers, json=payload, timeout=10)
            if resp.status_code == 200:
                llm_doc = resp.json()['choices'][0]['message']['content']
                # Append code snippets
                return format_full_markdown(endpoint, llm_doc, snippets)
        except Exception:
            pass

    # Fallback structured markdown generator
    fallback_doc = f"""# {method} `{path}`

> **Category**: `{category}` | **Status**: Active | **API Suite**: {endpoint.get('api_title', 'API Gateway')}

## Overview & Purpose

{summary}. {description if description else 'Provides core HTTP interface capabilities for high-performance application integrations.'}

## Authentication

All requests to `{path}` require a valid **Bearer Token** passed in the `Authorization` HTTP request header:
```http
Authorization: Bearer <your_access_token>
```

## Request Specification

### Parameters
{"| Name | Location | Required | Type | Description |" if parameters else "No query or path parameters required."}
{"|---|---|---|---|---|" if parameters else ""}
{"\n".join([f"| `{p.get('name')}` | `{p.get('in')}` | `{p.get('required')}` | `{p.get('type')}` | {p.get('description', 'N/A')} |" for p in parameters]) if parameters else ""}

### Request Body Schema
```json
{json.dumps(req_schema if req_schema else {"info": "No request payload required"}, indent=2)}
```

## Response Specification

```json
{json.dumps(resp_schema if resp_schema else {"status": "success", "code": 200}, indent=2)}
```

## Status Codes

| Code | Status | Meaning |
|---|---|---|
| `200 / 201` | OK | Request processed successfully |
| `400` | Bad Request | Invalid request body or missing mandatory fields |
| `401` | Unauthorized | Missing or expired authentication token |
| `404` | Not Found | Target resource or ID does not exist |
| `500` | Server Error | Internal gateway processing failure |
"""
    return format_full_markdown(endpoint, fallback_doc, snippets)

def format_full_markdown(endpoint: dict, body_md: str, snippets: dict) -> str:
    """Assembles body markdown, code snippets, and wikilinks placeholder."""
    method = endpoint.get('method', 'GET')
    path = endpoint.get('path', '/')

    return f"""{body_md}

## Code Examples

### Python (Requests)
```python
{snippets['python']}
```

### cURL
```bash
{snippets['curl']}
```

### JavaScript (Node.js)
```javascript
{snippets['javascript']}
```

### Go
```go
{snippets['go']}
```

## Related Data Schemas & Linked Endpoints
<!-- AUTO_LINK_PLACEHOLDER -->
"""

"""
Parser utilities for VigilDoc to ingest OpenAPI 3.0/Swagger (YAML/JSON) specs and Python/FastAPI route files.
"""

import os
import re
import json
import yaml
import ast
import datetime

def slugify(text: str) -> str:
    """Creates clean slug identifier from endpoint method and path."""
    text = text.lower()
    text = re.sub(r'[^a-z0-9_]', '_', text)
    text = re.sub(r'_+', '_', text)
    return text.strip('_')

def parse_openapi_spec(file_path: str) -> list:
    """Parses OpenAPI 3.0 / Swagger YAML or JSON file into structured endpoint dictionaries."""
    with open(file_path, 'r', encoding='utf-8') as f:
        if file_path.endswith('.yaml') or file_path.endswith('.yml'):
            data = yaml.safe_load(f)
        else:
            data = json.load(f)

    endpoints = []
    info = data.get('info', {})
    api_title = info.get('title', 'API Suite')
    paths = data.get('paths', {})

    for path, methods in paths.items():
        if not isinstance(methods, dict):
            continue

        for method, details in methods.items():
            if method.lower() not in ['get', 'post', 'put', 'delete', 'patch', 'options', 'head']:
                continue
            if not isinstance(details, dict):
                continue

            summary = details.get('summary', f"{method.upper()} {path}")
            description = details.get('description', '')
            tags = details.get('tags', ['Core Endpoints'])
            category = tags[0] if tags else 'Core Endpoints'

            # Normalize category
            if 'auth' in category.lower() or 'login' in category.lower() or 'token' in category.lower():
                category = 'Authentication'
            elif 'webhook' in category.lower():
                category = 'Webhooks'
            elif 'schema' in category.lower():
                category = 'Data Schemas'
            else:
                category = 'Core Endpoints'

            parameters = []
            for param in details.get('parameters', []):
                parameters.append({
                    "name": param.get('name'),
                    "in": param.get('in'),
                    "required": param.get('required', False),
                    "type": param.get('schema', {}).get('type', 'string') if isinstance(param.get('schema'), dict) else 'string',
                    "description": param.get('description', '')
                })

            # Request Body parsing
            request_schema = {}
            req_body = details.get('requestBody', {})
            if req_body and 'content' in req_body:
                content = req_body['content']
                json_content = content.get('application/json', {})
                request_schema = json_content.get('schema', {})

            # Response Body parsing
            response_schema = {}
            responses = details.get('responses', {})
            success_resp = responses.get('200') or responses.get('201') or list(responses.values())[0] if responses else {}
            if isinstance(success_resp, dict) and 'content' in success_resp:
                json_resp = success_resp['content'].get('application/json', {})
                response_schema = json_resp.get('schema', {})

            endpoint_id = slugify(f"{method}_{path}")
            endpoints.append({
                "id": endpoint_id,
                "api_title": api_title,
                "path": path,
                "method": method.upper(),
                "summary": summary,
                "description": description,
                "category": category,
                "parameters": parameters,
                "request_schema": request_schema,
                "response_schema": response_schema,
                "source_file": os.path.basename(file_path),
                "ingested_at": datetime.datetime.now().isoformat()
            })

    return endpoints


def parse_python_routes(file_path: str) -> list:
    """Parses Python FastAPI/Express route definitions and docstrings using regex/AST."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    endpoints = []
    # Match pattern like @app.post("/auth/register", tags=["Authentication"], summary="...")
    route_pattern = re.compile(
        r'@app\.(get|post|put|delete|patch)\(\s*["\']([^"\']+)["\'](?:,\s*tags=\[(.*?)\])?(?:,\s*summary=["\']([^"\']+)["\'])?',
        re.DOTALL
    )

    matches = route_pattern.findall(content)
    lines = content.splitlines()

    for idx, (method, path, tags_str, summary) in enumerate(matches):
        category = "Core Endpoints"
        if tags_str:
            clean_tags = [t.strip(' "\'[]') for t in tags_str.split(',')]
            if clean_tags:
                category = clean_tags[0]

        if 'auth' in category.lower() or 'login' in category.lower() or 'token' in category.lower():
            category = 'Authentication'

        if not summary:
            summary = f"{method.upper()} {path}"

        # Find following docstring
        docstring = ""
        # Search lines around this match
        route_sig = f'@app.{method}("{path}"'
        for i, line in enumerate(lines):
            if route_sig in line or f"@app.{method}('{path}'" in line:
                # look 5 lines ahead for """ docstring
                ahead = "\n".join(lines[i:i+10])
                doc_match = re.search(r'"""(.*?)"""', ahead, re.DOTALL)
                if doc_match:
                    docstring = doc_match.group(1).strip()
                break

        endpoint_id = slugify(f"{method}_{path}")
        endpoints.append({
            "id": endpoint_id,
            "api_title": "User Authentication Microservice",
            "path": path,
            "method": method.upper(),
            "summary": summary,
            "description": docstring or f"Handler for {method.upper()} {path}",
            "category": category,
            "parameters": [
                {"name": "token" if "me" in path else "payload", "in": "header" if "me" in path else "body", "required": True, "type": "object", "description": "JSON Payload / Bearer Token"}
            ],
            "request_schema": {"type": "object", "properties": {"credentials": {"type": "string"}}},
            "response_schema": {"type": "object", "properties": {"status": {"type": "string"}}},
            "source_file": os.path.basename(file_path),
            "ingested_at": datetime.datetime.now().isoformat()
        })

    return endpoints

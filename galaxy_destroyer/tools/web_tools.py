"""Web tools for Galaxy Destroyer"""

import json
import re
import urllib.request
import urllib.parse
import urllib.error
from typing import Any, Dict, Optional

from galaxy_destroyer.tools.registry import register_tool, ToolCategory, ToolParameter


def _fetch_url(url: str, timeout: int = 30) -> Dict[str, Any]:
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "GalaxyDestroyer/1.0 (Python Terminal)",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
            },
        )
        with urllib.request.urlopen(req, timeout=timeout) as response:
            content = response.read().decode("utf-8", errors="replace")
            return {
                "url": url,
                "status": response.status,
                "content": content[:50000],
                "content_length": len(content),
            }
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP Error: {e.code}", "url": url}
    except urllib.error.URLError as e:
        return {"error": f"URL Error: {e.reason}", "url": url}
    except Exception as e:
        return {"error": str(e), "url": url}


@register_tool(
    name="web_fetch",
    description="Fetch content from a URL",
    category=ToolCategory.WEB,
    parameters=[
        ToolParameter(name="url", description="URL to fetch", required=True),
        ToolParameter(name="prompt", description="What to extract from the page"),
    ],
)
def web_fetch(url: str, prompt: Optional[str] = None, _context: Any = None) -> Dict:
    result = _fetch_url(url)

    if "error" in result:
        return result

    content = result.get("content", "")

    if prompt:
        content = _extract_with_prompt(content, prompt)

    return {
        "url": url,
        "content": content,
        "content_length": len(content),
    }


def _extract_with_prompt(content: str, prompt: str) -> str:
    lines = content.split("\n")
    keywords = prompt.lower().split()

    relevant_lines = []
    for line in lines:
        line_lower = line.lower()
        if any(kw in line_lower for kw in keywords):
            relevant_lines.append(line.strip())

    if relevant_lines:
        return "\n".join(relevant_lines[:50])

    return content[:10000]


@register_tool(
    name="web_search",
    description="Search the web for information",
    category=ToolCategory.WEB,
    parameters=[
        ToolParameter(name="query", description="Search query", required=True),
        ToolParameter(
            name="num_results",
            description="Number of results",
            type="number",
            default=10,
        ),
    ],
)
def web_search(query: str, num_results: int = 10, _context: Any = None) -> Dict:
    try:
        encoded_query = urllib.parse.quote(query)
        search_url = f"https://html.duckduckgo.com/html/?q={encoded_query}"

        result = _fetch_url(search_url)

        if "error" in result:
            search_url = f"https://www.google.com/search?q={encoded_query}"
            result = _fetch_url(search_url)

        if "error" in result:
            return {
                "query": query,
                "error": result["error"],
                "results": [],
            }

        content = result.get("content", "")
        results = _parse_search_results(content, num_results)

        return {
            "query": query,
            "results": results,
            "count": len(results),
        }
    except Exception as e:
        return {"error": str(e), "query": query}


def _parse_search_results(html: str, num_results: int) -> list:
    results = []

    patterns = [
        r'<a class="result__a" href="([^"]+)">([^<]+)</a>',
        r'<h3 class="result__title">.*?href="([^"]+)">([^<]+)</a>.*?</h3>',
        r'<div class="resultsnippet">([^<]+)</div>',
    ]

    urls = re.findall(r'href="(https?://[^"]+)"', html)
    titles = re.findall(r"<h3[^>]*>([^<]+)</h3>", html)
    snippets = re.findall(r'class="[^"]*snippet[^"]*">([^<]+)', html)

    seen_urls = set()
    for i, url in enumerate(urls[: num_results * 2]):
        if url in seen_urls:
            continue
        if "google.com" in url or "duckduckgo" in url:
            continue

        seen_urls.add(url)

        title = titles[i] if i < len(titles) else url
        snippet = snippets[i] if i < len(snippets) else ""

        results.append(
            {
                "url": url,
                "title": re.sub(r"<[^>]+>", "", title).strip(),
                "snippet": re.sub(r"<[^>]+>", "", snippet).strip()[:200],
            }
        )

        if len(results) >= num_results:
            break

    return results


@register_tool(
    name="search_memory",
    description="Search through memories",
    category=ToolCategory.MEMORY,
    parameters=[
        ToolParameter(name="query", description="Search query", required=True),
    ],
)
def search_memory(query: str, _context: Any = None) -> Dict:
    from core.memory import get_auto_mem_path, ENTRYPOINT_NAME
    import os
    import re

    mem_path = get_auto_mem_path()
    results = []

    if not os.path.exists(mem_path):
        return {"query": query, "results": [], "message": "No memories found"}

    query_lower = query.lower()

    for root, dirs, files in os.walk(mem_path):
        dirs[:] = [d for d in dirs if not d.startswith(".")]

        for filename in files:
            if not filename.endswith(".md"):
                continue

            filepath = os.path.join(root, filename)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()

                if query_lower in content.lower():
                    lines = content.split("\n")
                    matches = []
                    for i, line in enumerate(lines, 1):
                        if query_lower in line.lower():
                            matches.append(f"Line {i}: {line.strip()[:100]}")

                    results.append(
                        {
                            "file": filename,
                            "path": filepath,
                            "matches": matches[:5],
                        }
                    )
            except Exception:
                pass

    return {
        "query": query,
        "results": results,
        "count": len(results),
    }

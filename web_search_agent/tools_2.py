"""
Tools for web_search_agent to use
"""

import requests
import os
from tavily import TavilyClient

MEMBERS = "https://members-api.parliament.uk/api"
GUARDIAN = "https://content.guardianapis.com"
tavily = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])


# ---- Finding MP website ----

def find_mp_site(mp_name):
    '''Finds an MP's personal website via the Parliament Members API'''

    r = requests.get(f"{MEMBERS}/Members/Search", params={"Name": mp_name, "take": 1}, timeout=30)
    r.raise_for_status()
    items = r.json().get("items", [])
    if not items:
        return {"error": f"No member found for '{mp_name}'"}
    member = items[0]["value"]

    r = requests.get(f"{MEMBERS}/Members/{member['id']}/Contact", timeout=30)
    r.raise_for_status()

    for contact in r.json().get("value", []):
        if contact.get("isWebAddress") or "website" in (contact.get("type") or "").lower():
            return {"name": member["nameDisplayAs"], "website": contact.get("line1")}

    return {"name": member["nameDisplayAs"], "website": None}

# ---- GUARDIAN SEARCH TOOL ----

def search_guardian(mp_name, topic, date_from=None, date_to=None, take=10):
    '''Search Guardian articles mentioning the MP and topic'''

    params = {
        "q": f'"{mp_name}" AND {topic}',      # quotes = exact name match
        "api-key": os.environ["GUARDIAN_API_KEY"],
        "page-size": take,
        "order-by": "newest",
        "show-fields": "trailText,bodyText",
    }
    if date_from:
        params["from-date"] = date_from
    if date_to:
        params["to-date"] = date_to

    r = requests.get(f"{GUARDIAN}/search", params=params, timeout=30)
    r.raise_for_status()
    results = r.json()["response"]["results"]

    return [
        {
            "source": "The Guardian",
            "title": a["webTitle"],
            "date": a["webPublicationDate"][:10],
            "url": a["webUrl"],
            "text": a.get("fields", {}).get("bodyText", "")[:1500],
        }
        for a in results
    ]


# ---- TAVILY search on BBC and PoliticsHome

SITES = {
    "bbc":          {"domain": "bbc.co.uk",        "topic": "news"},
    "politicshome": {"domain": "politicshome.com", "topic": "general"},
}

def search_site(mp_name, topic, site, domain=None, date_from=None, date_to=None, take=5):
    '''Search the BBC or PoliticsHome for an MP's statements on a topic'''

    config = SITES.get(site, {"domain": domain, "topic": "general"})
    params = {
        "query": f'"{mp_name}" {topic}',
        "include_domains": [config["domain"]],
        "topic": config["topic"],
        "search_depth": "basic",
        "max_results": take,
        "chunks_per_source": 2,
    }
    if date_from:
        params["start_date"] = date_from
    if date_to:
        params["end_date"] = date_to

    response = tavily.search(**params)

    return [
        {
            "source": site,
            "title": res.get("title"),
            "date": res.get("published_date"),
            "url": res.get("url"),
            "text": res.get("content", ""),
        }
        for res in response.get("results", [])
    ]


def read_article(url, topic):
    '''Fetch the parts of an article most relevant to the topic'''

    response = tavily.extract(urls=url, query=topic, chunks_per_source=3)
    results = response.get("results", [])
    if not results:
        return {"error": f"Could not extract {url}"}
    return {"url": url, "text": results[0].get("raw_content", "")}


# ---- SCHEMAS ----

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_site",
            "description": (
                "Search the BBC or PoliticsHome or a politicians official page for articles quoting or written by an MP on a topic. "
                "Returns title, date (may be null), url and a text excerpt."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "mp_name": {"type": "string"},
                    "topic": {"type": "string"},
                    "site": {"type": "string", "enum": ["bbc", "politicshome", "mp_site"]},
                    "domain": {"type": "string", "description": "Required when site is 'mp_site': the domain from find_mp_site, e.g. 'edmiliband.org'"},
                    "date_from": {"type": "string", "description": "yyyy-mm-dd"},
                    "date_to": {"type": "string", "description": "yyyy-mm-dd"},
                    "take": {"type": "integer", "description": "Max results (default 5)"},
                },
                "required": ["mp_name", "topic", "site"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_article",
            "description": "Fetch the most relevant passages of an article by url, when the search excerpt isn't enough.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string"},
                    "topic": {"type": "string"},
                },
                "required": ["url", "topic"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "find_mp_site",
            "description": (
                "Look up an MP's personal website via the Parliament Members API. "
                "Returns their official name and website url (null if none listed)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "mp_name": {"type": "string"},
                },
                "required": ["mp_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_guardian",
            "description": (
                "Search the Guardian news site via API page for articles quoting or written by an MP on a topic. "
                "Returns title, date (may be null), url and a text excerpt."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "mp_name": {"type": "string"},
                    "topic": {"type": "string"},
                    "date_from": {"type": "string", "description": "yyyy-mm-dd"},
                    "date_to": {"type": "string", "description": "yyyy-mm-dd"},
                    "take": {"type": "integer", "description": "Max results (default 10)"},
                },
                "required": ["mp_name", "topic"],
            },
        },
    },
]

FUNCS = {"search_guardian": search_guardian, 
         "search_site": search_site, 
         "read_article": read_article, 
         "find_mp_site": find_mp_site}

'''
Tools for Hansard Agent to use
'''

import re
import requests

HANSARD = "https://hansard-api.parliament.uk"

def search_parliament(
        search_term,
        date_from,
        date_to,
        house = None,
        take = 10
) -> str:
    '''Search Hansard for relevant speeches to user query'''

    params = {
        "queryParameters.searchTerm": search_term,
        "queryParameters.take": take,
        "queryParameters.orderBy": "SittingDateDesc",
    }
    if house:
        params["queryParameters.house"] = house
    if date_from:
        params["queryParameters.startDate"] = date_from
    if date_to:
        params["queryParameters.endDate"] = date_to


    r = requests.get(f"{HANSARD}/search/contributions/Spoken.json", params=params, timeout=30)
    r.raise_for_status()
    results = r.json().get("Results", [])   

    return [
        {
            "member": c.get("MemberName") or c.get("AttributedTo"),
            "date": (c.get("SittingDate") or "")[:10],
            "house": c.get("House"),
            "debate": c.get("DebateSection"),
            "debate_id": c.get("DebateSectionExtId"),
            "text": (c.get("ContributionTextFull") or c.get("ContributionText") or "")[:800],
        }
        for c in results
    ]


def get_debate(debate_id, max_chars = 8000):
    r = requests.get(f"{HANSARD}/debates/debate/{debate_id}.json", timeout=30)
    r.raise_for_status()
    d = r.json()
    lines = []
    for item in d.get("Items", []):
        text = re.sub(r"<[^>]+>", "", item.get("Value") or "").strip()
        if text:
            who = item.get("AttributedTo") or ""
            lines.append(f"{who}: {text}" if who else text)
    title = (d.get("Overview") or {}).get("Title", "")

    return {"title": title, "transcript": "\n".join(lines)[:max_chars]}

# --- Describing the tools for Hansard Agent --- 

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_parliament",
            "description": (
                "Search UK Hansard for spoken contributions in Parliament. "
                "search_term supports directives joined with AND: "
                "'spokenby:<name>', 'debate:<title text>', 'words:<words>'. "
                "Returns member, date, house, debate title, debate_id and text excerpt."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "search_term": {"type": "string"},
                    "house": {"type": "string", "enum": ["Commons", "Lords"]},
                    "start_date": {"type": "string", "description": "yyyy-mm-dd"},
                    "end_date": {"type": "string", "description": "yyyy-mm-dd"},
                    "take": {"type": "integer", "description": "Max results (default 10)"},
                },
                "required": ["search_term"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_debate",
            "description": "Fetch the transcript of a debate section using a debate_id from search_contributions.",
            "parameters": {
                "type": "object",
                "properties": {"debate_id": {"type": "string"}},
                "required": ["debate_id"],
            },
        },
    },
]
 
FUNCS = {"search_parliament": search_parliament, "get_debate": get_debate}
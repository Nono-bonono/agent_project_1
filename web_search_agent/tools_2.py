"""
Tools for web_search_agent to use
"""

import requests
import re

MEMBERS = "https://members-api.parliament.uk/api"

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
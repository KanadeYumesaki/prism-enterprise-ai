import re
from typing import Dict


def detect_domain(message: str) -> str:
    m = message.lower()
    if any(k in m for k in ["株", "株価", "株式", "finance", "投資"]):
        return "finance"
    if any(k in m for k in ["医療", "病院", "health", "medical"]):
        return "medical"
    if any(k in m for k in ["法律", "契約", "legal", "law"]):
        return "legal"
    if any(k in m for k in ["ニュース", "速報", "weather", "天気"]):
        return "news"
    return "general"


def detect_pii(message: str) -> Dict:
    patterns = {
        "email": r"[\w\.-]+@[\w\.-]+\.[a-zA-Z]{2,}",
        "phone": r"(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{2,4}\)?[-.\s]?)?\d{3,4}[-.\s]?\d{3,4}",
    }
    detected = []
    for name, pat in patterns.items():
        if re.search(pat, message):
            detected.append(name)
    return {"pii_detected": len(detected) > 0, "detected_types": detected}


def decide_mode(message: str, policies: Dict, domain: str, pii_flags: Dict) -> str:
    # If PII detected, escalate to HEAVY if rule exists
    if pii_flags.get("pii_detected"):
        for rule in policies.get("escalation_rules", []):
            if rule.get("name") == "pii_always_heavy":
                return rule.get("escalate_to_min_mode", "HEAVY")

    # Keyword-based matching from modes
    for mode in policies.get("modes", []):
        triggers = mode.get("triggers", {})
        # domains_any
        for d in triggers.get("domains_any", []) or []:
            if d in domain:
                return mode.get("id")
        # keywords_any
        for kw in triggers.get("keywords_any", []) or []:
            if kw in message:
                return mode.get("id")
        # fallback
        if triggers.get("fallback"):
            fallback_mode = mode.get("id")

    # if nothing matches, prefer FAST
    return "FAST"


def select_model(mode: str, policies: Dict) -> str:
    # Check routing rules first
    for r in policies.get("routing", {}).get("rules", []):
        when = r.get("when_mode_in", []) or []
        if mode in when:
            return r.get("primary_model")

    # Fallback to mode default_models
    for m in policies.get("modes", []):
        if m.get("id") == mode:
            defs = m.get("default_models", [])
            if defs:
                return defs[0]

    # Final fallback
    return "openai:gpt4_mini"

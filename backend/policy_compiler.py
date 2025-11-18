from typing import Dict


def build_system_prompt(mode: str, policies: Dict) -> str:
    base = [
        "You are an AI assistant governed by a central policy kernel.",
        "Follow the safety precedence as provided by the policy.",
    ]

    mode_info = None
    for m in policies.get("modes", []):
        if m.get("id") == mode:
            mode_info = m
            break

    if mode_info:
        if mode == "HEAVY":
            base.append("Be extremely cautious, especially for medical/legal/finance queries.")
        if mode == "FLASH":
            base.append("Focus on the most recent facts and keep the answer short. Avoid long advice.")
        if mode == "FAST":
            base.append("Respond quickly and concisely. Do not perform web searches.")

    # Add a sanitized summary of important safety rules
    safety = policies.get("safety", {})
    if safety:
        prec = safety.get("precedence", [])
        if prec:
            base.append("Safety precedence: " + ", ".join(prec))

    return "\n".join(base)

import re
from typing import Dict
from presidio_analyzer import AnalyzerEngine
from presidio_analyzer.nlp_engine import NlpEngineProvider

# ===== Presidio Analyzer Initialization (Global Scope) =====
# This is initialized once at module load time to avoid repeated model loading
# Uses ja_core_news_lg for high-accuracy Japanese NLP

_ANALYZER_ENGINE = None

def _get_analyzer_engine() -> AnalyzerEngine:
    """
    Lazy initialization of Presidio AnalyzerEngine with Japanese NLP model.
    Returns cached instance after first call to avoid reloading.
    """
    global _ANALYZER_ENGINE
    if _ANALYZER_ENGINE is None:
        # Configure NLP engine with Japanese spacy model
        config = {
            "nlp_engine_name": "spacy",
            "models": [
                {"lang_code": "ja", "model_name": "ja_core_news_lg"},
                {"lang_code": "en", "model_name": "en_core_web_sm"}  # Fallback for English
            ]
        }
        provider = NlpEngineProvider(nlp_configuration=config)
        nlp_engine = provider.create_engine()
        
        # Create analyzer engine
        _ANALYZER_ENGINE = AnalyzerEngine(nlp_engine=nlp_engine)
    
    return _ANALYZER_ENGINE


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
    """
    Detect PII (Personally Identifiable Information) using Microsoft Presidio.
    
    Uses NLP-based entity recognition with Japanese language model (ja_core_news_lg)
    for high-accuracy context-aware detection.
    
    Args:
        message: Input text to analyze
        
    Returns:
        Dict with:
            - pii_detected: bool, True if any PII found
            - detected_types: list of detected entity types
            
    Example:
        >>> detect_pii("私の名前は山田太郎です。電話番号は090-1234-5678です。")
        {'pii_detected': True, 'detected_types': ['PERSON', 'PHONE_NUMBER']}
    """
    try:
        analyzer = _get_analyzer_engine()
        
        # Entity types to detect
        # PERSON: 人名
        # PHONE_NUMBER: 電話番号
        # EMAIL_ADDRESS: メールアドレス
        # LOCATION: 住所・地名
        # CREDIT_CARD: クレジットカード番号
        entities_to_detect = [
            "PERSON",
            "PHONE_NUMBER", 
            "EMAIL_ADDRESS",
            "LOCATION",
            "CREDIT_CARD"
        ]
        
        # Analyze text (auto-detect language: ja or en)
        results = analyzer.analyze(
            text=message,
            language="ja",  # Primary language
            entities=entities_to_detect,
            score_threshold=0.4  # Confidence threshold: 40%以上のみ検知
        )
        
        # Extract unique entity types
        detected_types = list(set([result.entity_type for result in results]))
        
        return {
            "pii_detected": len(detected_types) > 0,
            "detected_types": detected_types
        }
        
    except Exception as e:
        # Fallback to regex-based detection if Presidio fails
        print(f"[WARN] Presidio PII detection failed: {e}. Falling back to regex.")
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

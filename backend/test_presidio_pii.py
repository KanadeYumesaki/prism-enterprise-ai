"""
Test script for Presidio-based PII detection in governance_kernel.py

Tests Japanese language PII detection with:
- PERSON (人名)
- PHONE_NUMBER (電話番号)
- EMAIL_ADDRESS (メールアドレス)
- LOCATION (住所・地名)
- CREDIT_CARD (クレジットカード番号)
"""

import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from governance_kernel import detect_pii


def test_japanese_pii_detection():
    """Test PII detection with Japanese text"""
    
    print("=" * 80)
    print("Presidio PII Detection Test - Japanese Language")
    print("=" * 80)
    print()
    
    # Test Case 1: Person + Phone + Location
    print("Test Case 1: Person Name + Phone Number + Location")
    print("-" * 80)
    text1 = "私の名前は山田太郎です。電話番号は090-1234-5678、住所は東京都港区です。"
    print(f"Input: {text1}")
    result1 = detect_pii(text1)
    print(f"Result: {result1}")
    print(f"Expected: PERSON, PHONE_NUMBER, LOCATION")
    print(f"✓ PASS" if all(e in result1["detected_types"] for e in ["PERSON", "PHONE_NUMBER", "LOCATION"]) else "✗ FAIL")
    print()
    
    # Test Case 2: Email Address
    print("Test Case 2: Email Address")
    print("-" * 80)
    text2 = "メールアドレスは yamada.taro@example.com です。"
    print(f"Input: {text2}")
    result2 = detect_pii(text2)
    print(f"Result: {result2}")
    print(f"Expected: EMAIL_ADDRESS")
    print(f"✓ PASS" if "EMAIL_ADDRESS" in result2["detected_types"] else "✗ FAIL")
    print()
    
    # Test Case 3: Credit Card
    print("Test Case 3: Credit Card Number")
    print("-" * 80)
    text3 = "カード番号は 4532-1234-5678-9010 です。"
    print(f"Input: {text3}")
    result3 = detect_pii(text3)
    print(f"Result: {result3}")
    print(f"Expected: CREDIT_CARD")
    print(f"✓ PASS" if "CREDIT_CARD" in result3["detected_types"] else "✗ FAIL")
    print()
    
    # Test Case 4: No PII (Clean Text)
    print("Test Case 4: No PII - Clean Business Text")
    print("-" * 80)
    text4 = "今日の会議では新しいプロジェクトについて議論します。"
    print(f"Input: {text4}")
    result4 = detect_pii(text4)
    print(f"Result: {result4}")
    print(f"Expected: No PII detected")
    print(f"✓ PASS" if not result4["pii_detected"] else "✗ FAIL")
    print()
    
    # Test Case 5: Multiple Entities
    print("Test Case 5: Complex Text with Multiple PII")
    print("-" * 80)
    text5 = """
    お客様情報:
    氏名: 佐藤花子
    電話: 03-1234-5678
    メール: hanako.sato@company.co.jp
    住所: 東京都渋谷区道玄坂1-2-3
    カード: 5555-4444-3333-2222
    """
    print(f"Input: {text5}")
    result5 = detect_pii(text5)
    print(f"Result: {result5}")
    print(f"Expected: PERSON, PHONE_NUMBER, EMAIL_ADDRESS, LOCATION, CREDIT_CARD")
    expected_entities = ["PERSON", "PHONE_NUMBER", "EMAIL_ADDRESS", "LOCATION", "CREDIT_CARD"]
    found_count = sum(1 for e in expected_entities if e in result5["detected_types"])
    print(f"Found {found_count}/{len(expected_entities)} expected entities")
    print(f"✓ PASS (>= 3 entities)" if found_count >= 3 else "✗ FAIL")
    print()
    
    # Test Case 6: English Text
    print("Test Case 6: English PII")
    print("-" * 80)
    text6 = "My name is John Smith. Call me at 555-1234. Email: john@example.com"
    print(f"Input: {text6}")
    result6 = detect_pii(text6)
    print(f"Result: {result6}")
    print(f"Expected: PERSON, PHONE_NUMBER, EMAIL_ADDRESS")
    print(f"✓ PASS" if result6["pii_detected"] else "✗ FAIL")
    print()
    
    print("=" * 80)
    print("Test Execution Complete")
    print("=" * 80)
    print()
    print("Note: Presidio uses NLP models which may have varying accuracy.")
    print("If some entities are not detected, it may be due to:")
    print("  - Low confidence score (< 0.4 threshold)")
    print("  - Context-dependent entity classification")
    print("  - Model limitations for specific entity types")
    print()


if __name__ == "__main__":
    try:
        test_japanese_pii_detection()
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

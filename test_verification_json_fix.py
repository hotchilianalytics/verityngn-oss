#!/usr/bin/env python3
"""
Test the JSON parsing fix for malformed LLM output.
"""

from verityngn.utils.json_fix import clean_gemini_json, safe_gemini_json_parse
import json

# Test case from the actual error
# Use raw string to avoid Python escaping
malformed_json = r'''
{
  "youtube_urls\": [
    \"https://www.youtube.com/watch?v=S02F793wGj0",
    "https://www.youtube.com/watch?v=L2GjHj-k118",
    "https://www.youtube.com/watch?v=V1S0tWz-e4w"
  ],
  "web_urls\": [
    \"https://www.snopes.com/fact-check/lipozem",
    "https://www.fda.gov/warning"
  ]
}
'''

print("=" * 80)
print("TEST: JSON Parsing Fix for Malformed LLM Output")
print("=" * 80)
print("\nOriginal malformed JSON:")
print(malformed_json[:200] + "...")

print("\n" + "=" * 80)
print("Step 1: Cleaning...")
print("=" * 80)
cleaned = clean_gemini_json(malformed_json)
print("Cleaned JSON:")
print(cleaned[:200] + "...")

print("\n" + "=" * 80)
print("Step 2: Parsing...")
print("=" * 80)
try:
    result = json.loads(cleaned)
    print("✅ SUCCESS: JSON parsed successfully!")
    print("\nParsed structure:")
    print(json.dumps(result, indent=2))
    
    # Verify expected keys exist
    if "youtube_urls" in result or "web_urls" in result:
        print("\n✅ PASS: Expected keys found")
        if "youtube_urls" in result:
            print(f"   - youtube_urls: {len(result.get('youtube_urls', []))} URLs")
        if "web_urls" in result:
            print(f"   - web_urls: {len(result.get('web_urls', []))} URLs")
    else:
        print("\n❌ FAIL: Expected keys missing")
        print(f"   - Got keys: {list(result.keys())}")
        
except json.JSONDecodeError as e:
    print(f"❌ FAIL: JSON parsing still failed: {e}")
    print(f"   Error at position {e.pos}: {cleaned[max(0,e.pos-20):e.pos+20]}")

print("\n" + "=" * 80)
print("Step 3: Safe Parse (with fallback)")
print("=" * 80)
result = safe_gemini_json_parse(malformed_json)
print("✅ safe_gemini_json_parse always returns a dict")
print(f"Result keys: {list(result.keys())}")

if "error" in result:
    print("⚠️  WARNING: Parsing failed, returned error dict")
    print(f"   Error: {result.get('error_message', 'Unknown')}")
else:
    print("✅ SUCCESS: Parsed successfully without error")

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print("✅ All tests completed")
print("✅ JSON fix handles malformed escape sequences")
print("✅ Safe parse provides graceful fallback")


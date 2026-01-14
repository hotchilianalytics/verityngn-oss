# Plan: Find and Verify Replacement Videos for Placeholders

## Overview

Replace 9 placeholder videos (using dQw4w9WgXcQ) with active YouTube videos that match the same profile/topic.

## Placeholder Videos to Replace

1. **Test ID 5**: Essential Oils - Health & Medicine / Alternative Medicine
2. **Test ID 7**: Coffeezilla Save the Kids Token Scam - Scams & Fraud / Cryptocurrency Scams
3. **Test ID 8**: Tinder Swindler - Scams & Fraud / Romance Scams
4. **Test ID 9**: Real Hustle Investment Scam - Scams & Fraud / Investment Scams
5. **Test ID 11**: Get Rich Quick - Finance & Investment / Investment Scams
6. **Test ID 12**: MLM Schemes - Finance & Investment / MLM/Pyramid Schemes
7. **Test ID 14**: BitConnect - Cryptocurrency / Scams
8. **Test ID 15**: Bitcoin $1M Prediction - Cryptocurrency / Price Predictions
9. **Test ID 16**: Absolute Proof - Politics & News / Election Fraud

## Approach

### Step 1: Manual Search for Each Topic
For each placeholder, search YouTube manually or use known video IDs:
- Use specific search terms matching the topic
- Look for well-known creators/channels (SciShow, Coffeezilla, John Oliver, etc.)
- Prefer educational/documentary content over promotional content
- Verify videos are public and accessible

### Step 2: Verify Video Activity
Use the verification script:
```bash
python scripts/find_replacement_videos.py --verify VIDEO_ID1 VIDEO_ID2 ...
```

### Step 3: Update test_videos.json
Once verified, update using:
```bash
python scripts/update_placeholder_videos.py --replacements '&#123;"5":"VIDEO_ID","7":"VIDEO_ID2",...&#125;'
```

## Suggested Video Sources

### Test ID 5: Essential Oils
- **SciShow**: Educational content about essential oils
- **Search**: "essential oils do they work" "SciShow"
- **Alternative**: "essential oils" "fact-checked" "health claims"

### Test ID 7: Coffeezilla Save the Kids
- **Coffeezilla Channel**: Known for crypto scam exposés
- **Search**: "Coffeezilla" "Save the Kids" "token"
- **Channel**: @Coffeezilla

### Test ID 8: Tinder Swindler
- **Netflix Official**: Official Netflix trailer
- **Search**: "Tinder Swindler" "Netflix" "official trailer"
- **Alternative**: Documentary channels covering the story

### Test ID 9: Real Hustle Investment Scam
- **BBC**: The Real Hustle episodes
- **Search**: "Real Hustle" "investment scam" "BBC"
- **Alternative**: Educational content about investment scams

### Test ID 11: Get Rich Quick
- **Coffeezilla**: Scam exposé videos
- **Search**: "get rich quick" "forex" "scam" "Coffeezilla"
- **Alternative**: Educational content debunking get-rich-quick schemes

### Test ID 12: MLM Schemes
- **John Oliver**: Last Week Tonight MLM episode
- **Search**: "MLM" "multi-level marketing" "John Oliver" "Last Week Tonight"
- **Alternative**: Documentary content about MLM/pyramid schemes

### Test ID 14: BitConnect
- **Coffeezilla**: BitConnect exposé
- **Search**: "BitConnect" "ponzi scheme" "Coffeezilla"
- **Alternative**: Documentary channels covering BitConnect

### Test ID 15: Bitcoin $1M Prediction
- **Search**: "Bitcoin" "$1 million" "prediction" "cryptocurrency"
- **Note**: Many videos exist, choose one with clear predictions

### Test ID 16: Absolute Proof
- **Mike Lindell**: Original video (if accessible)
- **Search**: "Absolute Proof" "Mike Lindell" "election fraud"
- **Alternative**: Fact-checking videos debunking the claims

## Verification Process

1. For each suggested video ID:
   ```bash
   python scripts/find_replacement_videos.py --verify VIDEO_ID
   ```

2. If verified, add to replacements JSON:
   ```json
   &#123;
     "5": "VERIFIED_VIDEO_ID",
     "7": "VERIFIED_VIDEO_ID",
     ...
   &#125;
   ```

3. Update test_videos.json:
   ```bash
   python scripts/update_placeholder_videos.py --replacements '&#123;"5":"VIDEO_ID",...&#125;' --dry-run
   python scripts/update_placeholder_videos.py --replacements '&#123;"5":"VIDEO_ID",...&#125;'
   ```

## Notes

- All videos must be publicly accessible (not private/unlisted)
- Videos should match the topic profile (category, subcategory, expected verdict)
- Prefer educational/documentary content over promotional content
- Verify videos are active before updating test_videos.json
- Update notes field to indicate video has been replaced


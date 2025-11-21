# Manual Process to Find Replacement Videos

Since automated search isn't providing specific video IDs, here's a manual process to find and verify replacement videos:

## Step-by-Step Process

### 1. For Each Placeholder Video:

**Test ID 5: Essential Oils**
- Go to YouTube and search: "essential oils do they work SciShow"
- Or: "essential oils fact-checked health claims"
- Find a video that matches the topic
- Copy the video ID from the URL (e.g., `https://www.youtube.com/watch?v=VIDEO_ID`)
- Verify it: `python scripts/find_replacement_videos.py --verify VIDEO_ID`

**Test ID 7: Coffeezilla Save the Kids**
- Go to YouTube and search: "Coffeezilla Save the Kids token"
- Or visit: https://www.youtube.com/@Coffeezilla
- Find the Save the Kids video
- Copy video ID and verify

**Test ID 8: Tinder Swindler**
- Go to YouTube and search: "Tinder Swindler Netflix official trailer"
- Find the official Netflix trailer
- Copy video ID and verify

**Test ID 9: Real Hustle Investment Scam**
- Go to YouTube and search: "Real Hustle investment scam BBC"
- Or: "Real Hustle fake investment"
- Find an episode or educational content
- Copy video ID and verify

**Test ID 11: Get Rich Quick**
- Go to YouTube and search: "get rich quick forex scam Coffeezilla"
- Or: "get rich quick investment scam exposé"
- Find a scam exposé video
- Copy video ID and verify

**Test ID 12: MLM Schemes**
- Go to YouTube and search: "John Oliver MLM Last Week Tonight"
- Or: "MLM pyramid scheme documentary"
- Find John Oliver's episode or similar content
- Copy video ID and verify

**Test ID 14: BitConnect**
- Go to YouTube and search: "BitConnect Coffeezilla ponzi scheme"
- Or: "BitConnect documentary exposé"
- Find a BitConnect exposé video
- Copy video ID and verify

**Test ID 15: Bitcoin $1M Prediction**
- Go to YouTube and search: "Bitcoin 1 million prediction 2024"
- Find a video with specific price predictions
- Copy video ID and verify

**Test ID 16: Absolute Proof**
- Go to YouTube and search: "Absolute Proof Mike Lindell"
- Or: "Absolute Proof debunked fact-check"
- Find the original or a fact-checking video
- Copy video ID and verify

### 2. Verify All Video IDs

Once you have candidate video IDs, verify them all at once:

```bash
python scripts/find_replacement_videos.py --verify VIDEO_ID1 VIDEO_ID2 VIDEO_ID3 ...
```

### 3. Update test_videos.json

Once you have verified video IDs, create a JSON mapping:

```json
{
  "5": "VERIFIED_VIDEO_ID_1",
  "7": "VERIFIED_VIDEO_ID_2",
  "8": "VERIFIED_VIDEO_ID_3",
  ...
}
```

Then update:

```bash
python scripts/update_placeholder_videos.py --replacements '{"5":"VIDEO_ID","7":"VIDEO_ID2",...}'
```

## Alternative: Use YouTube Data API

If you have a YouTube Data API key, you can use the API to search programmatically. See the scripts for examples of how to use the API.


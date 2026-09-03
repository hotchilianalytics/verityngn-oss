# YouTube captions (`.en.vtt`) — operator guide

VerityNgn does **not** download arbitrary public-video captions via the YouTube Data API metadata call alone. The working path is:

1. **Cached** `outputs/{video_id}/analysis/{video_id}.en.vtt` (or `.vendor.vtt` / `.gemini.vtt`)
2. **yt-dlp** with `player_client=android` and a fresh `cookies.txt`
3. **youtube_transcript_api** (often empty on current YouTube — PoToken rollout)
4. **Supadata** (paid, opt-in) — set `SUPADATA_API_KEY` in `.env`; writes `{id}.vendor.vtt`
5. **Groq ASR** (paid last resort) — set `GROQ_API_KEY`
6. **Gemini YouTube URL** (synthetic `.gemini.vtt` — not official captions)

## Why captions are hard (2025–2026)

| Symptom | Root cause |
|---------|------------|
| HTTP 200 + empty body from `timedtext` | YouTube **Proof-of-Origin token (PoToken)** required when caption `baseUrl` contains `&exp=xpe` |
| `youtube_transcript_api` returns nothing | Same PoToken gate; cookies do not mint `pot=` |
| `TranscriptsDisabled` on videos with visible captions | Often **IP block**, not disabled captions |
| YouTube Data API key “works” but no VTT | `videos.list` is metadata-only; `captions.download` needs **owner OAuth** |
| yt-dlp SABR / “not available on this app” | Default web/tv clients; use `CAPTION_PLAYER_CLIENT=android` + fresh cookies |

**Messaging lock:** A YouTube API key gives title/duration, **not** `.en.vtt` for third-party videos.

## Setup

1. Export `cookies.txt` from a logged-in browser ([yt-dlp wiki](https://github.com/yt-dlp/yt-dlp/wiki/Extractors#exporting-youtube-cookies)).
2. Place at repo root **or** `ui/cookies.txt` **or** set `YTDLP_COOKIES=/path/to/cookies.txt`.
3. Verify:

```bash
verityngn captions 'https://www.youtube.com/watch?v=tLJC8hkK-ao'
```

4. Refresh cookies when yt-dlp returns SABR / “not available on this app”.
5. If all scrapers fail, enable Gemini fallback (requires `VERITY_GEMINI_KEY`):

```bash
export CAPTION_GEMINI_FALLBACK=1   # default on
verityngn captions 'https://www.youtube.com/watch?v=VIDEO_ID'
# writes outputs/VIDEO_ID/analysis/VIDEO_ID.gemini.vtt (synthetic)
```

## Environment knobs

| Variable | Default | Purpose |
|----------|---------|---------|
| `YTDLP_COOKIES` | — | Absolute path to Netscape cookies file |
| `CAPTION_PLAYER_CLIENT` | `android` | yt-dlp YouTube player client |
| `SUPADATA_API_KEY` | — | Paid native/generate transcript (T-TX-002) |
| `GROQ_API_KEY` | — | Whisper ASR last resort |
| `TRANSCRIPT_PROVIDERS` | `cached,ytdlp,api,supadata,asr,gemini` | Ordered chain |
| `TRANSCRIPT_MAX_COST_USD` | `0.05` | Paid spend guard |
| `TRANSCRIPT_ALLOW_GENERATE` | `0` | Allow Supadata `mode=generate` for C4 |
| `CAPTION_GEMINI_FALLBACK` | `1` | Gemini YouTube URL transcript when scrapers fail |
| `CAPTION_GEMINI_MODEL` | `gemini-2.5-flash` | Model for synthetic transcript |
| `SKIP_LIVE_CAPTION_FETCH` | — | Set `1` for cache-only (CI); skips yt-dlp and Gemini |

## Module

`verityngn.services.video.caption_fetch.fetch_and_cache_vtt(video_id, url, output_dir)` returns:

```json
{
  "success": true,
  "vtt_path": "outputs/VIDEO_ID/analysis/VIDEO_ID.en.vtt",
  "text": "[00:01] ...",
  "source": "cached_vtt|yt-dlp|youtube_transcript_api|supadata|asr_groq|gemini_youtube",
  "synthetic": false,
  "errors": []
}
```

When `source=gemini_youtube`, `vtt_path` ends in `.gemini.vtt` and `synthetic=true`.  
When `source=supadata`, `vtt_path` ends in `.vendor.vtt` (never clobbers `.en.vtt`).

## Replacements we do NOT ship in OSS

| Option | Notes |
|--------|-------|
| YouTube Captions API OAuth | Owner-only |
| BotGuard / `bgutils` PoToken minting | Fragile, ToS-adjacent |

Paid adapters (**Supadata**, **Groq ASR**) are shipped but **opt-in via env keys** with a hard `TRANSCRIPT_MAX_COST_USD` budget. T-TX-002 v2: Supadata native **4/6** live.

## Tiers that use captions

| Tier | Captions |
|------|----------|
| `light` | VTT/vendor/Gemini → DR-direct |
| `full` | VTT cache before full pipeline |
| `auto` | Preflight → light or full |
| `local-light` | Sidecar `.vtt` / `.srt` on mp4 |
| `local-full` | Full pipeline on file |

## Honest messaging

- Gemini fallback ≠ YouTube's official caption file.
- Supadata native ≠ always unlock caption-less IR (Basler still C4 under free-tier 429).
- VSL videos (e.g. Lipozem) are spoken-heavy — weak multimodal proof (T-ABL-004).

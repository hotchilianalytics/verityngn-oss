"""
YouTube Search Module for VerityNgn
Provides YouTube video search functionality for counter-intelligence analysis.
"""

import logging
import isodate
from datetime import datetime
from typing import List, Dict, Any, Optional
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from verityngn.config.settings import (
    YOUTUBE_API_KEY,
    YOUTUBE_API_SERVICE_NAME,
    YOUTUBE_API_VERSION,
    YOUTUBE_SEARCH_MODE,
    YOUTUBE_DISABLE_V3,
    CI_ENHANCEMENT_ENABLED,
    YT_CI_MAX_QUERIES,
    YT_CI_PER_QUERY_RESULTS,
    YT_CI_TOTAL_RESULTS,
    AGENT_MODEL_NAME,
    OUTPUTS_DIR,
)
from verityngn.utils.llm_utils import build_langchain_vertex_kwargs

logger = logging.getLogger(__name__)


def _get_ytdlp_cookie_options() -> Dict[str, Any]:
    """Get yt-dlp options for cookie-based authentication.
    
    FIX: YouTube blocks yt-dlp with "Sign in to confirm you're not a bot".
    Adding cookie support helps avoid this.
    
    Returns:
        Dict of yt-dlp options for cookie handling
    """
    import os
    
    cookie_options = {}
    
    # Check for cookies.txt in various locations
    cookie_paths = [
        os.environ.get('YOUTUBE_COOKIES_PATH', ''),
        '/tmp/cookies.txt',
        'cookies.txt',
        os.path.expanduser('~/.config/yt-dlp/cookies.txt'),
        os.path.expanduser('~/cookies.txt'),
    ]
    
    for cookie_path in cookie_paths:
        if cookie_path and os.path.exists(cookie_path):
            logger.info(f"[YTDLP] Using cookies from: {cookie_path}")
            cookie_options['cookiefile'] = cookie_path
            break
    
    # Add bot-detection mitigations
    cookie_options.update({
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
        },
        'nocheckcertificate': True,
        'source_address': '0.0.0.0',
        # Graceful degradation on auth failures
        'ignoreerrors': True,
    })
    
    return cookie_options


class YouTubeSearchService:
    """Service for searching YouTube videos."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize YouTube search service."""
        self.api_key = api_key or YOUTUBE_API_KEY
        self.youtube = None
        
        # Initialize API client only if explicitly requested
        if YOUTUBE_SEARCH_MODE == "api" and not YOUTUBE_DISABLE_V3:
            if not self.api_key:
                logger.warning("YouTube API key not found. Falling back to yt-dlp search mode.")
                self.youtube = None
            else:
                try:
                    self.youtube = build(
                        YOUTUBE_API_SERVICE_NAME,
                        YOUTUBE_API_VERSION,
                        developerKey=self.api_key,
                    )
                    logger.info("YouTube API service initialized successfully (api mode)")
                except Exception as e:
                    logger.error(f"Failed to initialize YouTube API service: {e}")
                    self.youtube = None
        else:
            # ytdlp mode: do not initialize API client
            logger.info("YouTube search mode set to 'ytdlp' (API client disabled)")
            self.youtube = None
    
    def is_available(self) -> bool:
        """Return True if the YouTube Data API client is initialized and available."""
        return self.youtube is not None

    def expand_channel_to_videos(self, channel_url: str, keywords: List[str], max_results: int = 3) -> List[Dict[str, Any]]:
        """Use yt-dlp to list channel videos and return ones matching keywords.

        This avoids YouTube Data API calls and focuses on channel-specific videos.
        """
        try:
            import yt_dlp
            logger.info(f"[YTDLP CHANNEL] Expanding channel: {channel_url}")
            # Ensure we hit the videos tab for handles
            url = channel_url
            if "/videos" not in url:
                if url.endswith('/'):
                    url = url + "videos"
                else:
                    url = url + "/videos"

            # FIX: Add cookie options to avoid "Sign in to confirm you're not a bot"
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': True,
                'skip_download': True,
                'playlistend': 40,  # inspect first N videos
                **_get_ytdlp_cookie_options(),
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
            entries = info.get('entries', []) if isinstance(info, dict) else []
            results: List[Dict[str, Any]] = []
            kw_l = [k.strip().lower() for k in keywords if k and isinstance(k, str)]
            for entry in entries:
                title = entry.get('title', '') or ''
                lower = title.lower()
                if any(k in lower for k in kw_l):
                    vid = entry.get('id') or ''
                    vurl = f"https://www.youtube.com/watch?v={vid}" if vid and not entry.get('url','').startswith('http') else entry.get('url','')
                    if vurl:
                        results.append({
                            'id': vid or vurl,
                            'title': title,
                            'description': entry.get('description','') or '',
                            'url': vurl,
                            'channel_title': entry.get('uploader', ''),
                            'channel_id': entry.get('channel_id', '') or '',
                            'view_count': int(entry.get('view_count') or 0)
                        })
                if len(results) >= max_results:
                    break
            logger.info(f"[YTDLP CHANNEL] Expanded {len(results)} videos from channel")
            return results
        except Exception as e:
            logger.warning(f"[YTDLP CHANNEL] Expansion failed for {channel_url}: {e}")
            return []

    def _fallback_search_ytdlp(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Fallback search using yt-dlp's ytsearch when API quota is exceeded or API unavailable."""
        try:
            import yt_dlp
            logger.info(f"[YTDLP FALLBACK] Searching YouTube via yt-dlp: '{query}' (max_results: {max_results})")
            
            # FIX: Use cookie options to avoid "Sign in to confirm you're not a bot" errors
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': True,
                'skip_download': True,
                'default_search': 'ytsearch',
                'noplaylist': True,
                'max_downloads': max_results,
                **_get_ytdlp_cookie_options(),  # Add cookie and bot-mitigation options
            }
            videos: List[Dict[str, Any]] = []
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(query, download=False)
                for entry in info.get('entries', [])[:max_results]:
                    vid = entry.get('id')
                    url = f"https://www.youtube.com/watch?v={vid}" if vid else entry.get('url', '')
                    videos.append({
                        'id': vid or entry.get('url', ''),
                        'title': entry.get('title', ''),
                        'description': entry.get('description', ''),
                        'url': url,
                        'channel_title': entry.get('uploader', ''),
                        'channel_id': entry.get('channel_id', ''),
                        'category_id': None,
                        'thumbnails': {},
                        'publish_time': entry.get('upload_date', ''),
                        'tags': entry.get('tags', []),
                        'duration': 0.0,
                        'view_count': int(entry.get('view_count') or 0),
                        'like_count': int(entry.get('like_count') or 0),
                        'dislike_count': 0,
                        'comment_count': int(entry.get('comment_count') or 0)
                    })
            logger.info(f"[YTDLP FALLBACK] Found {len(videos)} videos")
            return videos
        except Exception as e:
            logger.error(f"[YTDLP FALLBACK] Error performing yt-dlp search: {e}")
            return []
    
    def fetch_video_metadata_ytdlp(self, video_id: str) -> Dict[str, Any]:
        """Fetch video metadata (title, description, tags, channel, etc.) via yt-dlp without downloading media.

        Args:
            video_id: YouTube video ID

        Returns:
            Dict with at least title, description, tags, uploader, channel_id
        """
        # First, try to load existing info.json locally to avoid API/yt-dlp calls
        import os
        import glob
        candidate_patterns = [
            f"sherlock_analysis_{video_id}/vngn_reports/{video_id}/analysis/{video_id}.info.json",
            f"{OUTPUTS_DIR.name}/{video_id}/**/{video_id}.info.json",
            f"downloads/{video_id}/{video_id}.info.json",
        ]
        for pattern in candidate_patterns:
            matches = glob.glob(pattern, recursive=True)
            if matches:
                try:
                    with open(matches[0], 'r', encoding='utf-8') as f:
                        import json as _json
                        info = _json.load(f)
                        return {
                            'title': info.get('title', ''),
                            'description': info.get('description', ''),
                            'tags': info.get('tags', []) or [],
                            'uploader': info.get('uploader', ''),
                            'channel_id': info.get('channel_id', ''),
                            'duration': info.get('duration', 0),
                            'view_count': info.get('view_count', 0),
                            'like_count': info.get('like_count', 0),
                            'comment_count': info.get('comment_count', 0),
                        }
                except Exception:
                    pass

        # Fallback to yt-dlp metadata extraction only if not found locally
        try:
            import yt_dlp
            url = f"https://www.youtube.com/watch?v={video_id}"
            # FIX: Add cookie options to avoid "Sign in to confirm you're not a bot"
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'skip_download': True,
                **_get_ytdlp_cookie_options(),
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
            return {
                'title': info.get('title', ''),
                'description': info.get('description', ''),
                'tags': info.get('tags', []) or [],
                'uploader': info.get('uploader', ''),
                'channel_id': info.get('channel_id', ''),
                'duration': info.get('duration', 0),
                'view_count': info.get('view_count', 0),
                'like_count': info.get('like_count', 0),
                'comment_count': info.get('comment_count', 0),
            }
        except Exception as e:
            logger.warning(f"[YTDLP META] Failed to fetch metadata for {video_id}: {e}")
            return {'title': f"Video {video_id}", 'description': '', 'tags': []}
    
    def search_videos(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Search for YouTube videos matching the specified query.
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return
            
        Returns:
            List of video information dictionaries
        """
        # Force yt-dlp when mode=ytdlp
        if YOUTUBE_SEARCH_MODE == "ytdlp" or not self.is_available():
            if self.youtube is None:
                logger.info("YouTube API not in use; using yt-dlp search")
            return self._fallback_search_ytdlp(query, max_results)
        
        # If API is disabled or unavailable, use yt-dlp search directly
        if YOUTUBE_DISABLE_V3 or not self.is_available():
            return self._fallback_search_ytdlp(query, max_results)
        
        try:
            # Simple on-process cache to avoid duplicate queries within TTL window
            from verityngn.config.settings import CACHE_ENABLED, YOUTUBE_API_TTL_HOURS
            cache_key = f"yt_api_search::{query}::{max_results}"
            if CACHE_ENABLED:
                try:
                    import time
                    if not hasattr(self, "_api_cache"):
                        self._api_cache = {}
                    entry = self._api_cache.get(cache_key)
                    if entry and (time.time() - entry[0] < YOUTUBE_API_TTL_HOURS * 3600):
                        logger.info("[YT API CACHE] Returning cached search results")
                        return entry[1]
                except Exception:
                    pass

            # Throttle slightly to avoid QPS spikes
            try:
                import time
                if not hasattr(self, "_last_api_call_ts"):
                    self._last_api_call_ts = 0.0
                elapsed = time.time() - self._last_api_call_ts
                if elapsed < 0.2:
                    time.sleep(0.2 - elapsed)
            except Exception:
                pass
            logger.info(f"Searching YouTube for: '{query}' (max_results: {max_results})")
            
            # Call the search.list method to retrieve results matching the specified query term
            search_response = self.youtube.search().list(
                q=query,
                part='snippet',
                maxResults=max_results,
                type='video'
            ).execute()
            
            # Extract video IDs
            video_ids = [item['id']['videoId'] for item in search_response.get('items', [])]
            
            if not video_ids:
                logger.info("No videos found for query")
                return []
            
            # Retrieve video statistics and additional metadata
            videos_response = self.youtube.videos().list(
                id=','.join(video_ids),
                part='snippet,contentDetails,statistics',
            ).execute()
            
            # Process the results
            videos = []
            for item in videos_response.get('items', []):
                try:
                    video = {
                        'id': item['id'],
                        'title': item['snippet']['title'],
                        'description': item['snippet']['description'],
                        'url': f"https://www.youtube.com/watch?v={item['id']}",
                        'channel_title': item['snippet']['channelTitle'],
                        'channel_id': item['snippet']['channelId'],
                        'category_id': item['snippet']['categoryId'],
                        'thumbnails': item['snippet']['thumbnails'],
                        'publish_time': item['snippet']['publishedAt'],
                        'tags': item['snippet'].get('tags', []),
                        'duration': self._parse_duration(item['contentDetails']['duration']),
                        'view_count': int(item['statistics'].get('viewCount', 0)),
                        'like_count': int(item['statistics'].get('likeCount', 0)),
                        'dislike_count': int(item['statistics'].get('dislikeCount', 0)),
                        'comment_count': int(item['statistics'].get('commentCount', 0))
                    }
                    videos.append(video)
                except Exception as e:
                    logger.warning(f"Error processing video item: {e}")
                    continue
            
            logger.info(f"Found {len(videos)} videos for query")
            try:
                self._last_api_call_ts = time.time()
            except Exception:
                pass
            if CACHE_ENABLED:
                try:
                    self._api_cache[cache_key] = (time.time(), videos)
                except Exception:
                    pass
            return videos
            
        except HttpError as e:
            logger.error(f"YouTube API HTTP error: {e}")
            # Attempt fallback if quota exceeded or any API error
            return self._fallback_search_ytdlp(query, max_results)
        except Exception as e:
            logger.error(f"Error searching YouTube: {e}")
            return self._fallback_search_ytdlp(query, max_results)
    
    def _parse_duration(self, duration_str: str) -> float:
        """Parse ISO 8601 duration string to seconds."""
        try:
            duration = isodate.parse_duration(duration_str)
            return duration.total_seconds()
        except Exception as e:
            logger.warning(f"Error parsing duration '{duration_str}': {e}")
            return 0.0

    def _extract_search_phrases_heuristic(self, video_title: str, initial_review_text: Optional[str] = None) -> List[str]:
        """Heuristically extract phrases (fallback)."""
        import re
        phrases: List[str] = []
        title_clean = (video_title or "").strip()
        if initial_review_text:
            quoted = re.findall(r'"([^"]{3,120})"|\'([^\']{3,120})\'', initial_review_text)
            for q in quoted:
                text = q[0] or q[1]
                text = re.sub(r"\s+", " ", text).strip()
                if 3 <= len(text) <= 120:
                    phrases.append(text)
            cap_sequences = re.findall(r'(?:\b[A-Z][a-zA-Z]+\b(?:\s+|\-)){1,3}\b[A-Z][a-zA-Z]+\b', initial_review_text)
            for cs in cap_sequences:
                cs_norm = re.sub(r"\s+", " ", cs).strip()
                if 3 <= len(cs_norm) <= 80 and cs_norm.lower() not in (title_clean.lower()):
                    phrases.append(cs_norm)
            topical_hits = re.findall(r'((?:weight\s+loss|turmeric|supplement|pills?|detox|metabolism|doctor|\bDr\.?\s+[A-Z][a-z]+|side\s+effects|clinical\s+trial|FDA|BBB|lawsuits?|complaints?))', (initial_review_text or ''), re.IGNORECASE)
            for th in topical_hits:
                phrases.append(th.strip())
        title_base = re.sub(r"(?i)(the\s+\d{1,2}\-second|shocking|amazing|incredible|secret|hack|exposed|revealed|202\d|official|new)\b[\w\s\-:!']*", "", title_clean).strip()
        if title_base and len(title_base.split()) <= 12:
            phrases.append(title_base)
        dr_names = re.findall(r'\bDr\.?\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?', video_title)
        phrases.extend(dr_names)
        seen: set = set()
        deduped: List[str] = []
        for p in phrases:
            key = p.lower()
            if key not in seen and 2 < len(p) < 120:
                deduped.append(p)
                seen.add(key)
        return deduped[:12]

    def _extract_search_phrases(self, video_title: str, initial_review_text: Optional[str] = None, video_id: Optional[str] = None) -> List[str]:
        """LLM-generated bespoke counter-intel phrases using Sherlock Mode.

        Uses Vertex LLM with inputs: title, description, tags, and optional initial_review_text.
        Falls back to heuristic extraction on failure.
        """
        # Gather metadata if we have video_id
        description = ""
        tags_list: List[str] = []
        if video_id:
            meta = self.fetch_video_metadata_ytdlp(video_id)
            if not video_title:
                video_title = meta.get('title', video_title)
            description = meta.get('description', '') or ''
            tags_list = meta.get('tags', []) or []

        try:
            from langchain_google_vertexai import VertexAI
            from langchain_core.prompts import ChatPromptTemplate
            from verityngn.utils.json_fix import parse_gemini_json, safe_gemini_json_parse
            llm = VertexAI(**build_langchain_vertex_kwargs(AGENT_MODEL_NAME, preferred_tokens=32768, temperature=0.2))
            prompt = ChatPromptTemplate.from_template(
                """
You are Sherlock Mode: generate bespoke counter-intelligence search phrases and candidate YouTube URLs to find reviews/debunks/warnings about a target video.

Return JSON with keys:
  "search_phrases": ["phrase1", ...]  // 10-25 high-signal queries
  "youtube_urls": ["https://www.youtube.com/watch?v=...", ...]  // optional direct review/debunk links

Inputs:
TITLE:
{title}

DESCRIPTION (may be truncated):
{description}

TAGS:
{tags}

INITIAL_REVIEW (optional):
{initial}

Guidelines:
- Focus on contra-claims: review, scam, debunk, exposed, warning, complaints, lawsuit, BBB, does not work
- Include product/brand/doctor aliases if present
- Avoid overly generic tokens (e.g., just "hack").
- Prefer combinations that will surface investigative content.
- Output only strict JSON; no commentary.
                """
            )
            msg = prompt.format_messages(
                title=video_title or "",
                description=description[:4000],
                tags=", ".join(tags_list)[:1000],
                initial=(initial_review_text or "")[:4000],
            )
            raw = llm.invoke(msg)
            # Extract text content from LLM response
            text = None
            try:
                # LangChain AIMessage typically has .content
                text = getattr(raw, "content", None) or (raw if isinstance(raw, str) else str(raw))
            except Exception:
                text = str(raw) if raw is not None else ""

            # Always use the safe parser first to avoid hard failures on empty/malformed output
            data = safe_gemini_json_parse(text or "")
            if not isinstance(data, dict) or not data or data.get("error"):
                # Try to extract the first JSON object if present
                import re as _re
                m = _re.search(r"\{[\s\S]*?\}\s*$", text) or _re.search(r"\{[\s\S]*\}", text)
                if m:
                    data = safe_gemini_json_parse(m.group(0))

            phrases = [p for p in (data.get("search_phrases", []) if isinstance(data, dict) else []) if isinstance(p, str)]
            urls = [u for u in data.get("youtube_urls", []) if isinstance(u, str)]

            # Save seed urls for later inclusion
            if video_id and urls:
                self._llm_seed_urls[video_id] = urls[:20]

            # Sanitize phrases: remove duplicates, repeated modifiers, overly-generic terms
            modifiers = [
                "review", "scam", "fake", "fraud", "debunk", "exposed",
                "doesn't work", "warning", "complaints", "lawsuit", "side effects",
                "truth", "myth", "fact check"
            ]
            generic_ban = {"hack", "official website"}
            def _clean_phrase(s: str) -> str:
                s = s.strip()
                # collapse whitespace
                import re as _re
                s = _re.sub(r"\s+", " ", s)
                # remove duplicate trailing modifier (e.g., "scam scam")
                for m in modifiers:
                    if s.lower().endswith(f" {m}"):
                        base = s[: -len(m)].strip()
                        # avoid base already endswith same mod
                        if base.lower().endswith(m):
                            s = base
                return s
            out: List[str] = []
            seen = set()
            for p in phrases:
                q = _clean_phrase(p)
                if not q or q.lower() in generic_ban:
                    continue
                if 2 < len(q) < 160 and q.lower() not in seen:
                    out.append(q)
                    seen.add(q.lower())
            if out:
                return out[:max(10, min(YT_CI_MAX_QUERIES, 25))]
        except Exception as e:
            logger.warning(f"[LLM PHRASES] Falling back to heuristic: {e}")

        return self._extract_search_phrases_heuristic(video_title or "", initial_review_text)

    def generate_counter_intelligence_queries(self, video_title: str, video_id: str, initial_review_text: Optional[str] = None) -> List[str]:
        """Generate multiple targeted queries using Sherlock-mode phrase extraction."""
        queries: List[str] = []
        seeds = self._extract_search_phrases(video_title, initial_review_text, video_id)
        modifiers = [
            "review", "scam", "fake", "fraud", "debunk", "exposed",
            "doesn't work", "warning", "complaints", "lawsuit", "side effects",
            "truth", "myth", "fact check"
        ]

        for seed in seeds[:6]:
            queries.append(seed)
            for mod in modifiers[:6]:
                queries.append(f"{seed} {mod}")

        if not seeds:
            words = video_title.split()[:4]
            title_excerpt = ' '.join(words)
            queries.extend([f"{title_excerpt} review", f"{title_excerpt} scam"]) 
        
        unique_queries: List[str] = []
        seen = set()
        for query in queries:
            q = query.strip()
            if q and q not in seen and len(q) < 300:
                unique_queries.append(q)
                seen.add(q)

        # Expand query count per settings, fallback to previous default (10)
        max_q = max(1, int(YT_CI_MAX_QUERIES or 10))
        return unique_queries[:max_q]

    def generate_counter_intelligence_query(self, video_title: str, video_id: str) -> str:
        """Generate a single search query (backward compatibility)."""
        queries = self.generate_counter_intelligence_queries(video_title, video_id)
        return queries[0] if queries else f"{video_title[:30]} review"

    def search_counter_intelligence(self, video_title: str, video_id: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Search for YouTube videos that might provide counter-intelligence using multiple targeted queries."""
        # Generate multiple targeted queries (title-only path)
        queries = self.generate_counter_intelligence_queries(video_title, video_id, None)
        
        # Collect results from all queries
        all_results = []
        seen_video_ids = set()
        
        # Cap total results to avoid runaway volume
        total_cap = max(5, int(YT_CI_TOTAL_RESULTS or 30))
        for query in queries:
            try:
                logger.info(f"Searching with query: '{query}'")
                # Use per-query breadth from settings
                per_q = max(1, int(YT_CI_PER_QUERY_RESULTS or 5))
                query_results = self.search_videos(query, max_results=per_q)
                
                # Deduplicate by video ID
                for video in query_results:
                    if video['id'] not in seen_video_ids:
                        seen_video_ids.add(video['id'])
                        all_results.append(video)
                        if len(all_results) >= total_cap:
                            logger.info(f"Reached total counter-intel cap ({total_cap}); stopping search loop")
                            break
                if len(all_results) >= total_cap:
                    break
                        
            except Exception as e:
                logger.warning(f"Query '{query}' failed: {e}")
                continue
        
        # Apply orthogonality filter based on title-only context
        all_results = self._filter_orthogonal_videos(video_title, "", all_results)
        
        if not all_results:
            logger.warning(f"No results found for any counter-intelligence queries")
            return []
        
        # Calculate counter-intelligence scores
        ranked_results = []
        for video in all_results:
            counter_score = self.calculate_counter_intelligence_score(video)
            video['counter_intelligence_score'] = counter_score
            ranked_results.append(video)
        
        # Remove likely shill/promotional videos
        ranked_results = [v for v in ranked_results if not self._is_promotional_shill(v)]
        
        # Sort by counter-intelligence score and view count
        ranked_results.sort(key=lambda x: (x['counter_intelligence_score'], x['view_count']), reverse=True)
        
        # FIXED: Lower threshold and add fallback logic
        # First try videos with score >= 0.5 (lowered from > 0)
        high_score_videos = [v for v in ranked_results if v['counter_intelligence_score'] >= 0.5]
        
        if len(high_score_videos) >= 3:
            return high_score_videos[:5]  # Return top 5 high-scoring videos
        
        # Fallback: If not enough high-scoring videos, include top videos regardless of score
        logger.info(f"Only {len(high_score_videos)} videos with score >= 0.5, using fallback")
        
        # Add top videos by view count that have any relevance (score > 0 OR contains key terms)
        fallback_videos = []
        for video in ranked_results:
            if video not in high_score_videos:
                title_lower = video.get('title', '').lower()
                if (video.get('counter_intelligence_score', 0) > 0 or 
                    any(term in title_lower for term in ['review', 'scam', 'fake', 'exposed', 'analysis', 'opinion', 'debunk', 'warning'])):
                    # Skip likely shill content
                    if not self._is_promotional_shill(video):
                        fallback_videos.append(video)
        
        # Combine high-scoring and fallback videos
        final_results = high_score_videos + fallback_videos
        selected_videos = final_results[:5]  # Return top 5 total
        
        # Optionally enhance with downloads; off by default for resource safety
        if CI_ENHANCEMENT_ENABLED:
            return self.enhance_counter_intelligence_with_detailed_analysis(selected_videos, video_id)
        return selected_videos

    def search_counter_intelligence_with_context(self, video_title: str, initial_review_text: Optional[str], video_id: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Sherlock-mode contextual search using title + initial review text for better queries."""
        queries = self.generate_counter_intelligence_queries(video_title, video_id, initial_review_text)
        all_results: List[Dict[str, Any]] = []
        seen_video_ids = set()

        total_cap = max(5, int(YT_CI_TOTAL_RESULTS or 30))
        for query in queries:
            try:
                logger.info(f"[SHERLOCK CTX] Searching with query: '{query}'")
                per_q = 2 # max(1, int(YT_CI_PER_QUERY_RESULTS or 5))
                query_results = self.search_videos(query, max_results=per_q)
                for video in query_results:
                    vid = video.get('id')
                    if vid and vid not in seen_video_ids:
                        seen_video_ids.add(vid)
                        all_results.append(video)
                        if len(all_results) >= total_cap:
                            logger.info(f"[SHERLOCK CTX] Reached total counter-intel cap ({total_cap}); stopping search loop")
                            break
                if len(all_results) >= total_cap:
                    break
            except Exception as e:
                logger.warning(f"[SHERLOCK CTX] Query '{query}' failed: {e}")
                continue

        # Filter out orthogonal results early to improve precision
        all_results = self._filter_orthogonal_videos(video_title, initial_review_text or "", all_results)

        if not all_results:
            logger.warning("[SHERLOCK CTX] No results for contextual queries; falling back to title-only")
            return self.search_counter_intelligence(video_title, video_id, max_results)

        ranked_results: List[Dict[str, Any]] = []
        for video in all_results:
            counter_score = self.calculate_counter_intelligence_score(video)
            video['counter_intelligence_score'] = counter_score
            ranked_results.append(video)

        ranked_results = [v for v in ranked_results if not self._is_promotional_shill(v)]
        ranked_results.sort(key=lambda x: (x['counter_intelligence_score'], x['view_count']), reverse=True)
        high_score_videos = [v for v in ranked_results if v['counter_intelligence_score'] >= 0.5]
        if len(high_score_videos) >= 3:
            return (
                self.enhance_counter_intelligence_with_detailed_analysis(high_score_videos[:5], video_id)
                if CI_ENHANCEMENT_ENABLED else high_score_videos[:5]
            )

        fallback_videos: List[Dict[str, Any]] = []
        for video in ranked_results:
            if video in high_score_videos:
                continue
            title_lower = video.get('title', '').lower()
            if (video.get('counter_intelligence_score', 0) > 0 or 
                any(term in title_lower for term in ['review', 'scam', 'fake', 'exposed', 'analysis', 'opinion', 'debunk', 'warning'])):
                fallback_videos.append(video)
        return (
            self.enhance_counter_intelligence_with_detailed_analysis(fallback_videos[:5], video_id)
            if CI_ENHANCEMENT_ENABLED else fallback_videos[:5]
        )

    def search_counter_intelligence_by_video_id(self, video_id: str, initial_review_text: Optional[str] = None, max_results: int = 10) -> List[Dict[str, Any]]:
        """Run counter-intel search deriving title/description/tags via yt-dlp using only video_id.

        Combines description and tags (and optional initial_review_text) as contextual seed for query generation.
        """
        meta = self.fetch_video_metadata_ytdlp(video_id)
        title = meta.get('title') or f"Video {video_id}"
        desc = meta.get('description', '') or ''
        tags_list = meta.get('tags', []) or []
        tags_text = ' '.join(tags_list)
        combined_context = ' '.join([s for s in [desc, tags_text, initial_review_text or ''] if s]).strip()
        return self.search_counter_intelligence_with_context(title, combined_context if combined_context else None, video_id, max_results)

    def _filter_orthogonal_videos(self, main_title: str, initial_review_text: str, videos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove results that are orthogonal (off-topic) to the original video context.

        Uses semantic filter if enabled and available; otherwise uses heuristics (seed match or token overlap).
        """
        import re
        from collections import Counter
        from verityngn.config.settings import SEMANTIC_FILTER_ENABLED, SEMANTIC_FILTER_THRESHOLD
        if SEMANTIC_FILTER_ENABLED:
            try:
                from verityngn.services.search.semantic_filter import is_on_topic
            except Exception as e:
                logger.warning(f"[SHERLOCK CTX] Semantic filter import failed, using heuristic: {e}")
                is_on_topic = None
        else:
            is_on_topic = None

        def tokenize(text: str) -> List[str]:
            text = text.lower()
            text = re.sub(r"[^a-z0-9\s]", " ", text)
            return [t for t in text.split() if len(t) >= 3]

        # Extract seeds from context
        # For filtering, use lightweight heuristic to avoid LLM latency
        seeds = [s.lower() for s in self._extract_search_phrases_heuristic(main_title or "", initial_review_text)[:8]]
        seed_words = set([w for s in seeds for w in tokenize(s)])

        ctx_tokens = set(tokenize((main_title or "") + " " + (initial_review_text or "")))
        if not ctx_tokens:
            return videos  # nothing to compare, skip filtering

        def jaccard(a: set, b: set) -> float:
            inter = len(a & b)
            uni = len(a | b)
            return (inter / uni) if uni else 0.0

        filtered: List[Dict[str, Any]] = []
        for v in videos:
            title = v.get('title', '')
            desc = v.get('description', '')
            text = f"{title} {desc}"
            vtoks = set(tokenize(text))

            # Seed hit or token overlap threshold
            seed_hit = any(sw in vtoks for sw in seed_words)
            overlap = jaccard(ctx_tokens, vtoks)

            keep = False
            if is_on_topic is not None:
                try:
                    keep = is_on_topic((main_title or "") + " " + (initial_review_text or ""), title, desc, SEMANTIC_FILTER_THRESHOLD)
                except Exception as e:
                    logger.warning(f"[SHERLOCK CTX] Semantic check failed, using heuristic: {e}")
                    keep = seed_hit or (overlap >= 0.06)
            else:
                keep = seed_hit or (overlap >= 0.06)

            if keep:
                filtered.append(v)
            else:
                logger.info(f"[SHERLOCK CTX] Filtering orthogonal video: '{title[:80]}' (overlap={overlap:.3f})")

        return filtered

    def enhance_counter_intelligence_with_detailed_analysis(self, videos: List[Dict[str, Any]], main_video_id: str) -> List[Dict[str, Any]]:
        """
        🎯 SHERLOCK ENHANCED: Download .info.json and .en.vtt files for counter-intelligence videos 
        and store them as DELIVERABLE files for end users.
        
        Immediately stores files when videos are decided for the counter-intel set.
        """
        import os
        import json
        from verityngn.services.video.downloader import VideoDownloader
        from verityngn.services.video.transcription import get_video_transcript
        
        logger.info(f"🚀 [SHERLOCK CI] ENHANCING {len(videos)} counter-intelligence videos with detailed analysis")
        logger.info(f"🎯 [SHERLOCK CI] Videos selected for counter-intel set - immediately downloading deliverables")
        
        # 🎯 SHERLOCK ENHANCEMENT: Create deliverable counter-intelligence directory structure
        # Store in multiple locations to ensure end-user access
        deliverable_locations = self._create_counter_intelligence_deliverable_structure(main_video_id)
        
        logger.info(f"📁 [SHERLOCK CI] Created deliverable locations:")
        for location_type, path in deliverable_locations.items():
            logger.info(f"   📂 {location_type}: {path}")
        
        enhanced_videos = []
        downloader = VideoDownloader()
        
        for i, video in enumerate(videos):
            try:
                video_id = video['id']
                video_url = f"https://www.youtube.com/watch?v={video_id}"
                
                logger.info(f"📥 [SHERLOCK CI] IMMEDIATELY downloading deliverables for counter-intel video {i+1}: {video['title'][:50]}...")
                
                # 🎯 SHERLOCK ENHANCEMENT: Store files in ALL deliverable locations for end-user access
                file_paths_by_location = {}
                
                # Download to each deliverable location
                for location_type, base_dir in deliverable_locations.items():
                    # Create individual directory for this counter-intelligence video in each location
                    video_counter_dir = os.path.join(base_dir, video_id)
                    os.makedirs(video_counter_dir, exist_ok=True)
                    
                    # Define file paths for this location
                    info_file_path = os.path.join(video_counter_dir, f"{video_id}.info.json")
                    vtt_file_path = os.path.join(video_counter_dir, f"{video_id}.en.vtt")
                    summary_file_path = os.path.join(video_counter_dir, f"{video_id}.summary.json")
                    
                    file_paths_by_location[location_type] = {
                        "info_file": info_file_path,
                        "vtt_file": vtt_file_path,
                        "summary_file": summary_file_path,
                        "directory": video_counter_dir
                    }
                
                # Use primary outputs location for the main download process
                primary_paths = file_paths_by_location["primary_outputs"]
                info_file_path = primary_paths["info_file"]
                vtt_file_path = primary_paths["vtt_file"]
                summary_file_path = primary_paths["summary_file"]
                
                # 🎯 SHERLOCK: Download metadata files to primary location
                import yt_dlp
                import shutil
                
                primary_dir = primary_paths["directory"]
                ydl_opts = {
                    'writeinfojson': True,
                    'writesubtitles': True,
                    'writeautomaticsub': True,
                    'subtitleslangs': ['en'],
                    'skip_download': True,  # Don't download video file - DELIVERABLE FOCUSED
                    'outtmpl': os.path.join(primary_dir, f'{video_id}.%(ext)s'),
                    'quiet': True,
                    'no_warnings': True
                }
                
                logger.info(f"🎯 [SHERLOCK CI] Downloading to primary deliverable location: {primary_dir}")
                # If files already exist in primary location, skip yt-dlp to avoid API usage
                needs_info = not os.path.exists(info_file_path)
                needs_vtt = not os.path.exists(vtt_file_path)
                if needs_info or needs_vtt:
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        ydl.download([video_url])
                else:
                    logger.info(f"🛑 [SHERLOCK CI] Skipping yt-dlp (files already present): {primary_dir}")
                
                # 🎯 SHERLOCK: Copy files to ALL other deliverable locations immediately
                logger.info(f"📋 [SHERLOCK CI] Copying files to all deliverable locations for end-user access")
                for location_type, paths in file_paths_by_location.items():
                    if location_type == "primary_outputs":
                        continue  # Skip primary - already downloaded there
                    
                    # Copy .info.json if it exists
                    if os.path.exists(info_file_path):
                        shutil.copy2(info_file_path, paths["info_file"])
                        logger.info(f"   ✅ Copied .info.json to {location_type}")
                    
                    # Copy .en.vtt if it exists  
                    if os.path.exists(vtt_file_path):
                        shutil.copy2(vtt_file_path, paths["vtt_file"])
                        logger.info(f"   ✅ Copied .en.vtt to {location_type}")
                
                # Extract detailed statistics from .info.json
                detailed_stats = {}
                if os.path.exists(info_file_path):
                    with open(info_file_path, 'r', encoding='utf-8') as f:
                        info_data = json.load(f)
                        detailed_stats = {
                            'view_count': info_data.get('view_count', 0),
                            'like_count': info_data.get('like_count', 0),
                            'comment_count': info_data.get('comment_count', 0),
                            'duration': info_data.get('duration', 0),
                            'upload_date': info_data.get('upload_date', ''),
                            'uploader': info_data.get('uploader', ''),
                            'uploader_id': info_data.get('uploader_id', ''),
                            'subscriber_count': info_data.get('uploader_subscriber_count', 0),
                            'description': info_data.get('description', ''),
                            'tags': info_data.get('tags', []),
                            'categories': info_data.get('categories', [])
                        }
                
                # Extract and analyze transcript from .en.vtt
                transcript_analysis = {}
                if os.path.exists(vtt_file_path):
                    try:
                        with open(vtt_file_path, 'r', encoding='utf-8') as f:
                            vtt_content = f.read()
                            # Parse VTT content to extract clean transcript
                            transcript_text = self._parse_vtt_transcript(vtt_content)
                            
                            if transcript_text:
                                # Analyze transcript for counter-intelligence content
                                transcript_analysis = self._analyze_counter_intelligence_transcript(
                                    transcript_text, video['title'], main_video_id
                                )
                    except Exception as e:
                        logger.warning(f"Error analyzing transcript for {video_id}: {e}")
                
                # 🚀 NEW: Generate comprehensive summary.json file
                stance = transcript_analysis.get('stance', 'neutral')
                confidence = transcript_analysis.get('confidence', 0.5)
                key_points = transcript_analysis.get('key_points', [])
                
                # 🎯 SHERLOCK: Create comprehensive summary data matching DEMO format exactly
                summary_data = {
                    "video_id": video_id,
                    "title": video['title'],
                    "description": detailed_stats.get('description', ''),
                    "url": video_url,
                    "channel_title": detailed_stats.get('uploader', ''),
                    "channel_id": detailed_stats.get('uploader_id', ''),
                    "category_id": video.get('category_id', ''),
                    "thumbnails": video.get('thumbnails', {}),
                    "publish_time": detailed_stats.get('upload_date', ''),
                    "tags": detailed_stats.get('tags', []),
                    "duration": detailed_stats.get('duration', 0),
                    "view_count": detailed_stats.get('view_count', 0),
                    "like_count": detailed_stats.get('like_count', 0),
                    "comment_count": detailed_stats.get('comment_count', 0),
                    "subscriber_count": detailed_stats.get('subscriber_count', 0),
                    "counter_intelligence_score": round(video.get('counter_intelligence_score', 0.0), 2),
                    # 🎯 DEMO Features: Enhanced analysis data
                    "stance": stance,
                    "confidence": confidence,
                    "key_points": key_points,
                    "transcript_length": transcript_analysis.get('transcript_length', 0),
                    "counter_signals": transcript_analysis.get('counter_signals', 0),
                    "supporting_signals": transcript_analysis.get('supporting_signals', 0),
                    "key_critical_phrases_found": transcript_analysis.get('key_critical_phrases_found', []),
                    "credibility_signals": transcript_analysis.get('credibility_signals', []),
                    "overall_stance": transcript_analysis.get('stance', 'neutral'),
                    "analysis_timestamp": datetime.now().isoformat(),
                    "files": {
                        "info_json": f"{video_id}.info.json",
                        "transcript": f"{video_id}.en.vtt",
                        "summary": f"{video_id}.summary.json"
                    },
                    # 🎯 DEMO: Additional statistics for comprehensive analysis
                    "upload_date": detailed_stats.get('upload_date', ''),
                    "uploader": detailed_stats.get('uploader', ''),
                    "uploader_id": detailed_stats.get('uploader_id', ''),
                    "categories": detailed_stats.get('categories', [])
                }
                
                # 🎯 SHERLOCK: Write summary.json file to ALL deliverable locations
                try:
                    # Write to primary location first
                    with open(summary_file_path, 'w', encoding='utf-8') as f:
                        json.dump(summary_data, f, indent=2, ensure_ascii=False)
                    logger.info(f"📄 [SHERLOCK CI] Generated summary file: {summary_file_path}")
                    
                    # Copy summary to all other locations
                    for location_type, paths in file_paths_by_location.items():
                        if location_type == "primary_outputs":
                            continue  # Skip primary - already written there
                        
                        try:
                            with open(paths["summary_file"], 'w', encoding='utf-8') as f:
                                json.dump(summary_data, f, indent=2, ensure_ascii=False)
                            logger.info(f"   ✅ Copied summary.json to {location_type}")
                        except Exception as e:
                            logger.warning(f"   ⚠️ Failed to copy summary to {location_type}: {e}")
                            
                except Exception as e:
                    logger.error(f"❌ Failed to write summary file: {e}")
                
                # 🎯 SHERLOCK: Enhanced video data with ALL deliverable locations
                enhanced_video = video.copy()
                enhanced_video.update({
                    'detailed_stats': detailed_stats,
                    'transcript_analysis': transcript_analysis,
                    'summary_data': summary_data,
                    'files_downloaded': {
                        'info_json': os.path.exists(info_file_path),
                        'vtt_transcript': os.path.exists(vtt_file_path),
                        'summary_json': os.path.exists(summary_file_path)
                    },
                    'deliverable_locations': file_paths_by_location,  # ALL locations for end-user access
                    'primary_counter_intel_directory': primary_paths["directory"],
                    'summary_file_path': summary_file_path,
                    'sherlock_deliverable_status': 'COMPLETED'  # Mark as deliverable ready
                })
                
                enhanced_videos.append(enhanced_video)
                logger.info(f"✅ Enhanced video {i+1} with detailed stats, transcript analysis, and summary file")
                
            except Exception as e:
                logger.error(f"❌ Failed to enhance video {i+1}: {e}")
                # Add original video without enhancement
                enhanced_videos.append(video)
        
        logger.info(f"🎯 Successfully enhanced {len([v for v in enhanced_videos if 'detailed_stats' in v])} of {len(videos)} counter-intelligence videos")
        return enhanced_videos

    def _create_counter_intelligence_deliverable_structure(self, main_video_id: str) -> Dict[str, str]:
        """
        🎯 SHERLOCK METHOD: Create deliverable directory structure for counter-intelligence files.
        
        Ensures files are stored where end users can access them as deliverables.
        """
        import os
        from verityngn.config.settings import OUTPUTS_DIR
        
        deliverable_locations = {}
        
        # Location 1: Primary outputs directory (main deliverable location)
        outputs_ci_dir = os.path.join(OUTPUTS_DIR, main_video_id, "counter_intelligence")
        os.makedirs(outputs_ci_dir, exist_ok=True)
        deliverable_locations["primary_outputs"] = outputs_ci_dir
        
        # Location 2: Sherlock analysis directory (for debugging/analysis)
        sherlock_ci_dir = os.path.join(f"sherlock_analysis_{main_video_id}", "counter_intelligence")
        os.makedirs(sherlock_ci_dir, exist_ok=True)
        deliverable_locations["sherlock_analysis"] = sherlock_ci_dir
        
        # Location 3: Timestamped outputs (if available in context)
        try:
            # Try to get the current timestamped directory if we're in report generation context
            timestamped_ci_dir = os.path.join(str(OUTPUTS_DIR), main_video_id, "latest", "counter_intelligence")
            os.makedirs(timestamped_ci_dir, exist_ok=True)
            deliverable_locations["timestamped_outputs"] = timestamped_ci_dir
        except:
            # If timestamped directory creation fails, continue without it
            pass
        
        return deliverable_locations

    def _parse_vtt_transcript(self, vtt_content: str) -> str:
        """Parse VTT file content to extract clean transcript text."""
        lines = vtt_content.split('\n')
        transcript_lines = []
        
        for line in lines:
            line = line.strip()
            # Skip VTT header, timestamps, and empty lines
            if (not line or 
                line.startswith('WEBVTT') or 
                '-->' in line or
                line.isdigit()):
                continue
            
            # Clean up the text
            clean_line = line.replace('<c>', '').replace('</c>', '').strip()
            if clean_line:
                transcript_lines.append(clean_line)
        
        return ' '.join(transcript_lines)

    def _analyze_counter_intelligence_transcript(self, transcript: str, video_title: str, main_video_id: str) -> Dict[str, Any]:
        """
        🎯 SHERLOCK ENHANCED: Analyze transcript content for counter-intelligence insights with DEMO-level detail.
        Provides stance detection, signal counting, and key phrase extraction matching DEMO files.
        """
        analysis = {
            'transcript_length': len(transcript),
            'key_phrases': [],
            'critical_points': [],
            'stance_indicators': {},
            'credibility_signals': [],
            # 🎯 DEMO Features: Match exact DEMO structure
            'stance': 'neutral',
            'confidence': 0.5,
            'counter_signals': 0,
            'supporting_signals': 0,
            'key_critical_phrases_found': [],  # DEMO format: "term": "context sentence"
            'transcript_text': transcript
        }
        
        if not transcript:
            return analysis
        
        transcript_lower = transcript.lower()
        
        # 🎯 SHERLOCK: Enhanced counter-intelligence phrases (matching DEMO)
        counter_phrases = [
            'scam', 'fake', 'fraud', 'lie', 'misleading', 'false', 'hoax',
            'doesn\'t work', 'waste of money', 'no results', 'ineffective',
            'red flags', 'warning', 'beware', 'avoid', 'not worth it',
            'overpriced', 'overhyped', 'disappointing', 'useless',
            'fabricated', 'deceptive', 'predatory', 'exposed', 'tactics'
        ]
        
        supporting_phrases = [
            'works', 'effective', 'results', 'recommend', 'good', 'helps',
            'success', 'positive', 'beneficial', 'worth it', 'legit'
        ]
        
        # 🎯 DEMO: Count signals exactly like DEMO files
        analysis['counter_signals'] = sum(transcript_lower.count(phrase) for phrase in counter_phrases)
        analysis['supporting_signals'] = sum(transcript_lower.count(phrase) for phrase in supporting_phrases)
        
        # 🎯 DEMO: Determine stance based on signal ratio
        total_signals = analysis['counter_signals'] + analysis['supporting_signals']
        if total_signals > 0:
            counter_ratio = analysis['counter_signals'] / total_signals
            if counter_ratio > 0.7:
                analysis['stance'] = 'counter'
                analysis['confidence'] = min(0.95, 0.6 + (counter_ratio - 0.7) * 1.17)
            elif counter_ratio < 0.3:
                analysis['stance'] = 'supporting'
                analysis['confidence'] = min(0.95, 0.6 + (0.3 - counter_ratio) * 1.17)
            else:
                analysis['stance'] = 'neutral'
                analysis['confidence'] = 0.5
        
        # 🎯 DEMO: Extract key critical phrases with context (matching DEMO format)
        for phrase in counter_phrases:
            if phrase in transcript_lower:
                # Find sentences containing this phrase for DEMO-style output
                sentences = transcript.split('.')
                for sentence in sentences:
                    if phrase in sentence.lower() and len(sentence.strip()) > 10:
                        # Format exactly like DEMO: "term": "context sentence..."
                        clean_sentence = sentence.strip()
                        if len(clean_sentence) > 80:
                            clean_sentence = clean_sentence[:80] + "..."
                        analysis['key_critical_phrases_found'].append(f'"{phrase}": {clean_sentence}')
                        break  # Only take first occurrence per phrase
        
        # Maintain backwards compatibility
        analysis['stance_indicators'] = {
            'counter_signals': analysis['counter_signals'],
            'supporting_signals': analysis['supporting_signals'],
            'overall_stance': analysis['stance']
        }
        
        # Extract key phrases (backwards compatibility)
        for phrase in counter_phrases + supporting_phrases:
            if phrase in transcript_lower:
                # Find context around the phrase
                index = transcript_lower.find(phrase)
                start = max(0, index - 50)
                end = min(len(transcript), index + len(phrase) + 50)
                context = transcript[start:end].strip()
                analysis['key_phrases'].append({
                    'phrase': phrase,
                    'context': context
                })
        
        # 🎯 SHERLOCK: Enhanced credibility signals (matching DEMO)
        credibility_terms = [
            'doctor', 'study', 'research', 'clinical trial', 'peer reviewed',
            'fda', 'evidence', 'scientific', 'medical', 'expert', 'professional',
            'investigation', 'review', 'analysis', 'fake', 'scam', 'warning', 
            'exposed', 'consumer', 'alert'
        ]
        
        for term in credibility_terms:
            if term in transcript_lower:
                analysis['credibility_signals'].append(term)
        
        return analysis

    def calculate_counter_intelligence_score(self, video: Dict[str, Any]) -> float:
        """Calculate a score for how likely a video is to contain counter-intelligence."""
        score = 0.0
        
        title = video.get('title', '').lower()
        description = video.get('description', '').lower()
        
        # EXPANDED: Counter-intelligence keywords with gentler terms
        counter_keywords = [
            # Strong negative terms
            'scam', 'fake', 'fraud', 'lie', 'lies', 'debunk', 'exposed', 'false claims',
            'misleading', 'deceptive', 'warning', 'beware', 'avoid', 'hoax',
            
            # Investigative terms  
            'investigation', 'fact check', 'myth', 'busted', 'truth', 'reality',
            
            # Gentler critical terms
            'doesn\'t work', 'not effective', 'waste of money', 'overhyped', 'overpriced',
            'no results', 'didn\'t work', 'useless', 'ineffective', 'disappointing',
            
            # Product-specific terms
            'supplement scam', 'weight loss fraud', 'diet scam', 'pill scam',
            
            # Cautionary terms
            'before you buy', 'think twice', 'be careful', 'watch out', 'red flags'
        ]
        
        # Check title and description for counter-intelligence terms
        for keyword in counter_keywords:
            if keyword in title:
                score += 2.0
            if keyword in description:
                score += 1.0
        
        # Boost score for high view count (more credible reviews tend to get more views)
        view_count = video.get('view_count', 0)
        if view_count > 100000:
            score += 1.0
        elif view_count > 10000:
            score += 0.5
        
        return score

    def _has_strong_negative(self, text_lower: str) -> bool:
        strong_terms = [
            'scam', 'fake', 'fraud', 'exposed', 'warning', "don't buy", 'avoid',
            'rip-off', 'ripoff', 'bbb', 'complaints', 'lawsuit', "doesn't work",
            'side effects', 'danger', 'unsafe', 'quack', 'debunk'
        ]
        return any(term in text_lower for term in strong_terms)

    def _is_promotional_shill(self, video: Dict[str, Any]) -> bool:
        """Detect likely promotional/shill videos using title/description heuristics."""
        title = (video.get('title') or '').lower()
        desc = (video.get('description') or '').lower()

        promo_terms = [
            'official', 'buy', 'order', 'discount', 'coupon', 'promo code', 'use code',
            'link in description', 'click link', 'free shipping', 'limited time',
            'today only', 'special offer', 'save', 'get yours', 'shop now', 'purchase'
        ]

        # If the video contains strong negatives, do not consider it shill
        if self._has_strong_negative(f"{title} {desc}"):
            return False

        # Plain 'review' with marketing signals is suspicious
        if 'review' in title and any(term in desc for term in promo_terms):
            return True

        # Titles with marketing terms without negatives
        if any(term in title for term in promo_terms):
            return True

        # Heavy call-to-action patterns
        cta_patterns = ['subscribe', 'like and subscribe', 'smash the like', 'giveaway']
        if any(p in desc for p in cta_patterns) and 'review' in title and not self._has_strong_negative(title):
            return True

        # Brand/product name repeated with 'official website'
        if 'official website' in title or 'official website' in desc:
            return True

        return False

    def analyze_video_stance(self, title: str, description: str, target_title: str) -> Dict[str, Any]:
        """Analyze a video's stance toward the target video (counter, confirming, or neutral)."""
        title_lower = title.lower()
        desc_lower = description.lower()
        
        # Counter-intelligence indicators
        counter_indicators = [
            'scam', 'fake', 'fraud', 'lie', 'lies', 'debunk', 'exposed', 'warning', 
            'beware', 'avoid', 'don\'t buy', 'misleading', 'deceptive', 'false'
        ]
        
        # Confirming indicators
        confirming_indicators = [
            'works', 'effective', 'great', 'amazing', 'recommended', 'success', 
            'results', 'proven', 'legitimate', 'real'
        ]
        
        counter_score = sum(1 for indicator in counter_indicators if indicator in title_lower or indicator in desc_lower)
        confirming_score = sum(1 for indicator in confirming_indicators if indicator in title_lower or indicator in desc_lower)
        
        key_points = []
        
        if counter_score > confirming_score and counter_score > 0:
            stance = 'counter'
            confidence = min(counter_score / 3.0, 1.0)  # Normalize to 0-1
            # Extract key counter points
            for indicator in counter_indicators:
                if indicator in title_lower:
                    key_points.append(f"Title mentions '{indicator}'")
                if indicator in desc_lower:
                    key_points.append(f"Description mentions '{indicator}'")
        elif confirming_score > counter_score and confirming_score > 0:
            stance = 'confirming'
            confidence = min(confirming_score / 3.0, 1.0)
            # Extract key confirming points
            for indicator in confirming_indicators:
                if indicator in title_lower:
                    key_points.append(f"Title mentions '{indicator}'")
                if indicator in desc_lower:
                    key_points.append(f"Description mentions '{indicator}'")
        else:
            stance = 'neutral'
            confidence = 0.1
            key_points = ['No clear stance detected']
        
        return {
            'stance': stance,
            'confidence': confidence,
            'key_points': key_points[:3]  # Limit to top 3 points
        }

    def analyze_evidence_content(self, videos: List[Dict[str, Any]], target_video_title: str) -> Dict[str, Any]:
        """Analyze YouTube video descriptions for counter or confirming information."""
        counter_evidence = []
        confirming_evidence = []
        
        for video in videos:
            title = video.get('title', '')
            description = video.get('description', '')
            url = video.get('url', '')
            view_count = video.get('view_count', 0)
            
            # Analyze description for stance
            analysis = self.analyze_video_stance(title, description, target_video_title)
            
            evidence_item = {
                'title': title,
                'url': url,
                'view_count': view_count,
                'stance': analysis['stance'],
                'confidence': analysis['confidence'],
                'key_points': analysis['key_points']
            }
            
            if analysis['stance'] == 'counter':
                counter_evidence.append(evidence_item)
            elif analysis['stance'] == 'confirming':
                confirming_evidence.append(evidence_item)
        
        return {
            'counter_evidence': counter_evidence,
            'confirming_evidence': confirming_evidence,
            'total_videos_analyzed': len(videos)
        }


# Global instance for easy access
youtube_search_service = YouTubeSearchService()

# Convenience functions for backward compatibility
def youtube_search(query: str, max_results: int = 10) -> List[Dict[str, Any]]:
    """Search YouTube videos (convenience function)."""
    return youtube_search_service.search_videos(query, max_results)

def search_youtube_counter_intelligence(video_title: str, video_id: str, max_results: int = 10) -> List[Dict[str, Any]]:
    """Search for YouTube counter-intelligence videos (convenience function)."""
    return youtube_search_service.search_counter_intelligence(video_title, video_id, max_results)

def analyze_youtube_evidence_content(videos: List[Dict[str, Any]], target_video_title: str) -> Dict[str, Any]:
    """Analyze YouTube evidence content (convenience function)."""
    return youtube_search_service.analyze_evidence_content(videos, target_video_title) 

def search_youtube_counter_intelligence_with_context(video_title: str, initial_review_text: Optional[str], video_id: str, max_results: int = 10) -> List[Dict[str, Any]]:
    """Contextual version leveraging initial review paragraphs for better queries."""
    return youtube_search_service.search_counter_intelligence_with_context(video_title, initial_review_text, video_id, max_results)
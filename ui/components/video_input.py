"""
Video Input Tab Component

Allows users to submit YouTube URLs for verification.
"""

import streamlit as st
import re
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from components.ui_debug import ui_debug_enabled, debug_write, debug_exception
from components.nav_utils import render_gallery_cta, go_to_gallery


def extract_video_id(url: str) -> str:
    """Extract video ID from YouTube URL."""
    # Strip whitespace from URL first
    url = url.strip()
    
    patterns = [
        r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([^&\n?#\s]+)',
        r'youtube\.com/shorts/([^&\n?#\s]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            video_id = match.group(1).strip()  # Strip any whitespace from video ID
            return video_id
    
    # Also try to extract just the video ID if it's provided directly
    # Pattern for 11-character video ID
    if len(url.strip()) == 11 and url.strip().replace('-', '').replace('_', '').isalnum():
        return url.strip()
    
    return None


def parse_channel_url(url: str) -> Optional[Dict[str, str]]:
    """
    Parse YouTube channel URL to extract channel identifier.
    
    Supports formats:
    - https://www.youtube.com/@NextMedHealth
    - https://www.youtube.com/@NextMedHealth/videos
    - https://www.youtube.com/channel/UC...
    - https://www.youtube.com/user/username
    
    Returns:
        Dict with 'type' ('handle', 'channel_id', 'username') and 'identifier', or None
    """
    if not url:
        return None
    
    url = url.strip()
    
    # Handle format: @username or /@username
    handle_match = re.search(r'youtube\.com/@([^/\s?#]+)', url)
    if handle_match:
        return {
            'type': 'handle',
            'identifier': handle_match.group(1),
            'url': url
        }
    
    # Channel ID format: /channel/UC...
    channel_id_match = re.search(r'youtube\.com/channel/([^/\s?#]+)', url)
    if channel_id_match:
        return {
            'type': 'channel_id',
            'identifier': channel_id_match.group(1),
            'url': url
        }
    
    # Legacy username format: /user/username
    username_match = re.search(r'youtube\.com/user/([^/\s?#]+)', url)
    if username_match:
        return {
            'type': 'username',
            'identifier': username_match.group(1),
            'url': url
        }
    
    return None


def is_channel_url(url: str) -> bool:
    """Check if URL is a channel URL (not a video URL)."""
    if not url:
        return False
    return parse_channel_url(url) is not None


def validate_youtube_url(url: str) -> tuple[bool, str]:
    """
    Validate YouTube URL (video or channel).
    
    Returns:
        (is_valid, message_or_id)
    """
    if not url:
        return False, "Please enter a URL"
    
    # Check if it's a channel URL
    if is_channel_url(url):
        return True, "channel"
    
    # Otherwise, validate as video URL
    video_id = extract_video_id(url)
    if not video_id:
        return False, "Invalid YouTube URL format"
    
    if len(video_id) != 11:
        return False, "Invalid video ID length"
    
    return True, video_id


def render_video_input_tab():
    """Render the video input tab."""
    
    st.header("🎬 Verify YouTube Video")

    # Reports CTA
    render_gallery_cta(key="open_gallery_from_verify")
    
    # Introduction
    st.markdown("""
    Enter a YouTube video URL to analyze its factual claims and assess truthfulness.
    The system will:
    
    1. **Download & Analyze** the video using multimodal AI
    2. **Extract Claims** from audio, visual text, and demonstrations
    3. **Search for Evidence** across the web
    4. **Generate Report** with truthfulness assessment
    """)
    
    st.markdown("---")
    
    def start_verification_callback():
        """Callback to handle verification start and tab switching."""
        # Get current input values
        # NOTE: We must use st.session_state to get values inside a callback
        # But simple variables are not available unless we use keys for widgets
        
        # For now, we set the flags to trigger processing in the next run
        st.session_state.processing_status = 'processing'
        # We need to ensure video_id is correct, but args are passed at render time
        # which is fine for the button click
        pass

    # Channel video fetching function
    @st.cache_data(ttl=300)  # Cache for 5 minutes
    def fetch_channel_videos(channel_url: str, max_results: int = 50) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """
        Fetch latest videos from a YouTube channel.
        
        Returns:
            (list of video dicts, error_message)
        """
        import os
        debug_write("DEBUG: fetch_channel_videos called")
        debug_write(f"DEBUG: Channel URL: {channel_url}")
        debug_write(f"DEBUG: max_results: {max_results}")
        
        # Helper function to get API key from Streamlit secrets or environment
        def get_youtube_api_key() -> Optional[str]:
            """Get YouTube API key from st.secrets (priority) or os.environ."""
            # Try Streamlit secrets first (for Streamlit Community Cloud)
            try:
                if hasattr(st, 'secrets') and 'YOUTUBE_API_KEY' in st.secrets:
                    return st.secrets['YOUTUBE_API_KEY']
            except Exception:
                pass
            
            # Fall back to environment variable
            return os.getenv('YOUTUBE_API_KEY')
        
        youtube_api_key = get_youtube_api_key()
        debug_write(f"DEBUG: YOUTUBE_API_KEY: {'SET' if youtube_api_key else 'NOT SET'}")
        
        try:
            channel_info = parse_channel_url(channel_url)
            debug_write(f"DEBUG: Parsed channel info: {channel_info}")
            if not channel_info:
                return [], "Invalid channel URL format"
            
            # For handles (@username), use yt-dlp directly (more reliable)
            # For channel IDs, try YouTube Data API first
            if channel_info['type'] == 'handle':
                # Use yt-dlp for handles - it's more reliable than API search
                debug_write("DEBUG: Using yt-dlp for @handle")
                try:
                    import yt_dlp
                    debug_write("DEBUG: yt-dlp imported successfully")
                    try:
                        debug_write(f"DEBUG: yt-dlp version: {yt_dlp.version.__version__}")
                    except Exception:
                        pass
                    
                    # Ensure we hit the videos tab
                    url = channel_url
                    if "/videos" not in url:
                        if url.endswith('/'):
                            url = url + "videos"
                        else:
                            url = url + "/videos"
                    
                    # Updated options for better channel extraction
                    debug = ui_debug_enabled()
                    ydl_opts = {
                        'quiet': not debug,
                        'no_warnings': not debug,
                        'extract_flat': 'in_playlist',  # Better for playlists/channels
                        'skip_download': True,
                        'playlistend': max_results,
                        'ignoreerrors': False,
                        'no_color': True,  # For cleaner Streamlit output
                    }
                    
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        debug_write(f"DEBUG: Extracting info from: {url}")
                        info = ydl.extract_info(url, download=False)
                    
                    debug_write(f"DEBUG: Info extracted, type: {type(info)}")
                    
                    # Debug: Show what keys are in the info dict
                    if isinstance(info, dict):
                        debug_write(f"DEBUG: Info dict keys: {list(info.keys())}")
                        debug_write(f"DEBUG: Info has 'entries': {'entries' in info}")
                        if 'entries' in info and info['entries']:
                            debug_write(f"DEBUG: First entry keys: {list(info['entries'][0].keys())}")
                    
                    entries = info.get('entries', []) if isinstance(info, dict) else []
                    debug_write(f"DEBUG: Found {len(entries)} entries")
                    videos = []
                    
                    for entry in entries[:max_results]:
                        vid = entry.get('id') or ''
                        if not vid:
                            continue
                        
                        vurl = f"https://www.youtube.com/watch?v={vid}"
                        title = entry.get('title', 'Untitled')
                        upload_date = entry.get('upload_date', '')
                        
                        # Format date if available (YYYYMMDD -> YYYY-MM-DD)
                        date_str = ''
                        if upload_date and len(upload_date) == 8:
                            try:
                                date_str = f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:8]}"
                            except:
                                date_str = upload_date
                        
                        videos.append({
                            'id': vid,
                            'title': title,
                            'url': vurl,
                            'publish_date': date_str,
                            'view_count': int(entry.get('view_count') or 0),
                            'description': entry.get('description', '')[:200] + '...' if len(entry.get('description', '')) > 200 else entry.get('description', '')
                        })
                    
                    debug_write(f"DEBUG: Processed {len(videos)} videos")
                    
                    # If no videos found, try alternative extraction method
                    if not videos:
                        debug_write("DEBUG: No videos with flat extraction, trying full extraction...")
                        try:
                            # Try without extract_flat (downloads more metadata but more reliable)
                            ydl_opts_full = {
                                'quiet': not debug,
                                'no_warnings': not debug,
                                'extract_flat': False,  # Full extraction
                                'skip_download': True,
                                'playlistend': max_results,
                                'ignoreerrors': True,  # Skip unavailable videos
                                'no_color': True,
                            }
                            
                            with yt_dlp.YoutubeDL(ydl_opts_full) as ydl:
                                debug_write(f"DEBUG: Full extraction from: {url}")
                                info_full = ydl.extract_info(url, download=False)
                            
                            if isinstance(info_full, dict):
                                debug_write(f"DEBUG: Full info keys: {list(info_full.keys())}")
                                entries_full = info_full.get('entries', [])
                                debug_write(f"DEBUG: Full extraction found {len(entries_full)} entries")
                                
                                for entry in entries_full[:max_results]:
                                    if not entry:  # Skip None entries
                                        continue
                                    vid = entry.get('id') or ''
                                    if not vid:
                                        continue
                                    
                                    vurl = f"https://www.youtube.com/watch?v={vid}"
                                    title = entry.get('title', 'Untitled')
                                    upload_date = entry.get('upload_date', '')
                                    
                                    date_str = ''
                                    if upload_date and len(upload_date) == 8:
                                        try:
                                            date_str = f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:8]}"
                                        except:
                                            date_str = upload_date
                                    
                                    videos.append({
                                        'id': vid,
                                        'title': title,
                                        'url': vurl,
                                        'publish_date': date_str,
                                        'view_count': int(entry.get('view_count') or 0),
                                        'description': entry.get('description', '')[:200] + '...' if len(entry.get('description', '')) > 200 else entry.get('description', '')
                                    })
                                
                                debug_write(f"DEBUG: Full extraction processed {len(videos)} videos")
                        except Exception as full_extract_error:
                            if ui_debug_enabled():
                                st.warning(f"Full extraction also failed: {full_extract_error}")
                    
                    if videos:
                        return videos, None
                    return [], "No videos found. Channel may be empty or private."
                    
                except Exception as ytdlp_error:
                    ytdlp_msg = str(ytdlp_error)
                    debug_exception(f"yt-dlp exception: {ytdlp_msg}", ytdlp_error)
                    if 'private' in ytdlp_msg.lower() or 'unavailable' in ytdlp_msg.lower():
                        return [], "Channel is private or unavailable."
                    elif 'not found' in ytdlp_msg.lower() or 'does not exist' in ytdlp_msg.lower():
                        return [], "Channel not found. Please check the channel URL."
                    else:
                        return [], f"Failed to fetch videos: {ytdlp_msg}"
            
            # Try YouTube Data API for channel IDs and legacy usernames
            try:
                from googleapiclient.discovery import build
                
                # Use the helper function to get API key
                api_key = get_youtube_api_key()
                if not api_key:
                    raise ValueError("YouTube API key not configured")
                
                youtube = build("youtube", "v3", developerKey=api_key)
                
                # Resolve channel identifier to channel ID
                channel_id = None
                if channel_info['type'] == 'channel_id':
                    channel_id = channel_info['identifier']
                elif channel_info['type'] == 'username':
                    # For handle (@username), try multiple approaches
                    # Approach 1: Try direct channel lookup by custom URL (may not work for all)
                    try:
                        # Note: YouTube API v3 doesn't directly support @handle lookup
                        # We'll use search as fallback
                        channels_response = youtube.channels().list(
                            forUsername=channel_info['identifier'],
                            part='id'
                        ).execute()
                        if channels_response.get('items'):
                            channel_id = channels_response['items'][0]['id']
                    except:
                        pass
                    
                    # Approach 2: Search for channel by handle name
                    if not channel_id:
                        try:
                            search_response = youtube.search().list(
                                q=channel_info['identifier'],
                                type='channel',
                                part='id,snippet',
                                maxResults=5
                            ).execute()
                            
                            # Try to find exact match by checking customUrl in snippet
                            if search_response.get('items'):
                                for item in search_response['items']:
                                    snippet = item.get('snippet', {})
                                    custom_url = snippet.get('customUrl', '')
                                    # Check if customUrl matches our handle (with or without @)
                                    if custom_url and (
                                        custom_url.lower() == f"@{channel_info['identifier'].lower()}" or
                                        custom_url.lower() == channel_info['identifier'].lower()
                                    ):
                                        channel_id = item['id']['channelId']
                                        break
                                
                                # If no exact match, use first result
                                if not channel_id:
                                    channel_id = search_response['items'][0]['id']['channelId']
                        except:
                            pass
                elif channel_info['type'] == 'username':
                    # Legacy username format
                    try:
                        channels_response = youtube.channels().list(
                            forUsername=channel_info['identifier'],
                            part='id'
                        ).execute()
                        if channels_response.get('items'):
                            channel_id = channels_response['items'][0]['id']
                    except:
                        pass
                
                # If handle type somehow got here (shouldn't happen), skip API
                if channel_info['type'] == 'handle':
                    raise ValueError("Handle should use yt-dlp, not API")
                
                if not channel_id:
                    raise ValueError("Could not resolve channel ID")
                
                # Get uploads playlist ID
                channels_response = youtube.channels().list(
                    id=channel_id,
                    part='contentDetails'
                ).execute()
                
                if not channels_response.get('items'):
                    raise ValueError("Channel not found")
                
                uploads_playlist_id = channels_response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
                
                # Get videos from uploads playlist
                playlist_items = []
                next_page_token = None
                
                while len(playlist_items) < max_results:
                    request = youtube.playlistItems().list(
                        playlistId=uploads_playlist_id,
                        part='snippet,contentDetails',
                        maxResults=min(50, max_results - len(playlist_items)),
                        pageToken=next_page_token
                    )
                    response = request.execute()
                    
                    playlist_items.extend(response.get('items', []))
                    next_page_token = response.get('nextPageToken')
                    
                    if not next_page_token:
                        break
                
                # Get video details
                video_ids = [item['contentDetails']['videoId'] for item in playlist_items[:max_results]]
                
                if not video_ids:
                    return [], "Channel has no videos"
                
                videos_response = youtube.videos().list(
                    id=','.join(video_ids),
                    part='snippet,statistics,contentDetails'
                ).execute()
                
                videos = []
                for item in videos_response.get('items', []):
                    snippet = item['snippet']
                    stats = item['statistics']
                    
                    # Parse publish date
                    publish_date = snippet.get('publishedAt', '')
                    try:
                        pub_dt = datetime.fromisoformat(publish_date.replace('Z', '+00:00'))
                        date_str = pub_dt.strftime('%Y-%m-%d')
                    except:
                        date_str = publish_date[:10] if len(publish_date) >= 10 else ''
                    
                    videos.append({
                        'id': item['id'],
                        'title': snippet['title'],
                        'url': f"https://www.youtube.com/watch?v={item['id']}",
                        'publish_date': date_str,
                        'view_count': int(stats.get('viewCount', 0)),
                        'description': snippet.get('description', '')[:200] + '...' if len(snippet.get('description', '')) > 200 else snippet.get('description', '')
                    })
                
                return videos, None
                
            except Exception as api_error:
                error_msg = str(api_error)
                # Check for specific API errors
                if 'quota' in error_msg.lower() or '429' in error_msg:
                    # Quota exceeded - fallback to yt-dlp
                    pass
                elif '403' in error_msg or 'forbidden' in error_msg.lower():
                    return [], "API access forbidden. Check your YouTube API key permissions."
                elif '404' in error_msg or 'not found' in error_msg.lower():
                    return [], "Channel not found. Please check the channel URL."
                elif 'invalid' in error_msg.lower():
                    return [], f"Invalid channel: {error_msg}"
                
                # Fallback to yt-dlp
                try:
                    import yt_dlp
                    
                    # Ensure we hit the videos tab
                    url = channel_url
                    if "/videos" not in url:
                        if url.endswith('/'):
                            url = url + "videos"
                        else:
                            url = url + "/videos"
                    
                    ydl_opts = {
                        'quiet': True,
                        'no_warnings': True,
                        'extract_flat': True,
                        'skip_download': True,
                        'playlistend': max_results,
                    }
                    
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(url, download=False)
                    
                    entries = info.get('entries', []) if isinstance(info, dict) else []
                    videos = []
                    
                    for entry in entries[:max_results]:
                        vid = entry.get('id') or ''
                        if not vid:
                            continue
                        
                        vurl = f"https://www.youtube.com/watch?v={vid}"
                        title = entry.get('title', 'Untitled')
                        upload_date = entry.get('upload_date', '')
                        
                        # Format date if available (YYYYMMDD -> YYYY-MM-DD)
                        date_str = ''
                        if upload_date and len(upload_date) == 8:
                            try:
                                date_str = f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:8]}"
                            except:
                                date_str = upload_date
                        
                        videos.append({
                            'id': vid,
                            'title': title,
                            'url': vurl,
                            'publish_date': date_str,
                            'view_count': int(entry.get('view_count') or 0),
                            'description': entry.get('description', '')[:200] + '...' if len(entry.get('description', '')) > 200 else entry.get('description', '')
                        })
                    
                    if videos:
                        return videos, None
                    else:
                        return [], "No videos found. Channel may be empty or private."
                    
                except Exception as ytdlp_error:
                    ytdlp_msg = str(ytdlp_error)
                    if 'private' in ytdlp_msg.lower() or 'unavailable' in ytdlp_msg.lower():
                        return [], "Channel is private or unavailable."
                    elif 'not found' in ytdlp_msg.lower() or 'does not exist' in ytdlp_msg.lower():
                        return [], "Channel not found. Please check the channel URL."
                    else:
                        return [], f"Failed to fetch videos. Error: {ytdlp_msg}"
        
        except Exception as e:
            debug_exception(f"Channel fetch failed: {str(e)}", e)
            return [], f"Error fetching channel videos: {str(e)}"
    
    # Main input section
    col1, col2 = st.columns([3, 1])
    
    # Initialize video_id at function scope
    video_id = None
    
    with col1:
        # Check if example URL was set
        default_url = st.session_state.get('example_url', '')
        if default_url:
            # Clear it so it doesn't persist
            st.session_state.pop('example_url', None)
        
        # Channel URL input section
        st.subheader("📺 Select from Channel")
        channel_url = st.text_input(
            "YouTube Channel URL",
            value=st.session_state.get('channel_url_input', ''),
            placeholder="https://www.youtube.com/@NextMedHealth",
            help="Enter a YouTube channel URL to browse its latest videos",
            key="channel_url_input"
        )
        
        # Reset video selection if channel URL changed
        if 'last_channel_url' not in st.session_state:
            st.session_state.last_channel_url = ''
        
        if channel_url != st.session_state.last_channel_url:
            st.session_state.last_channel_url = channel_url
            st.session_state.channel_video_select = 0  # Reset selection
            if not channel_url:
                st.session_state.pop('video_url_input', None)  # Clear video URL if channel cleared
        
        # Channel video selection
        selected_video_url = None
        if channel_url:
            channel_info = parse_channel_url(channel_url)
            if channel_info:
                with st.spinner("Fetching channel videos..."):
                    videos, error = fetch_channel_videos(channel_url, max_results=50)
                
                if error:
                    st.error(f"❌ {error}")
                elif videos:
                    st.success(f"✅ Found {len(videos)} videos")
                    
                    # Create dropdown options
                    video_options = ["-- Select a video --"] + [
                        f"{vid['title'][:60]}{'...' if len(vid['title']) > 60 else ''} - {vid['publish_date']} - {vid['view_count']:,} views"
                        for vid in videos
                    ]
                    
                    selected_index = st.selectbox(
                        "Select Video",
                        range(len(video_options)),
                        format_func=lambda x: video_options[x],
                        key="channel_video_select"
                    )
                    
                    if selected_index > 0:  # Not the placeholder
                        selected_video = videos[selected_index - 1]
                        selected_video_url = selected_video['url']
                        # Update session state so video_url_input gets the value
                        st.session_state['video_url_input'] = selected_video_url
                        st.info(f"Selected: **{selected_video['title']}**")
                else:
                    st.warning("No videos found for this channel")
            elif channel_url.strip():
                st.error("❌ Invalid channel URL format. Use format: https://www.youtube.com/@ChannelName")
        
        st.markdown("---")
        st.subheader("🎬 Or Enter Video URL Directly")
        
        # Video URL input
        # Initialize video_url_input in session state if not present
        if 'video_url_input' not in st.session_state:
            st.session_state['video_url_input'] = default_url
        
        # Update from selected video if available
        if selected_video_url:
            st.session_state['video_url_input'] = selected_video_url
        
        video_url = st.text_input(
            "YouTube Video URL",
            value=st.session_state.get('video_url_input', ''),
            placeholder="https://www.youtube.com/watch?v=...",
            help="Enter the full YouTube video URL or select from channel above",
            key="video_url_input"
        )
        
        # Validate URL in real-time
        if video_url:
            is_valid, result = validate_youtube_url(video_url)
            if is_valid:
                if result == "channel":
                    st.info("ℹ️ Channel URL detected. Use the channel selector above to browse videos.")
                    video_id = None
                else:
                    st.success(f"✅ Valid video ID: `{result}`")
                    video_id = result
            else:
                st.error(f"❌ {result}")
                video_id = None
    
    with col2:
        st.markdown("### 💡 Tips")
        st.info("""
        **Channel Selection:**
        - Enter a channel URL like `@NextMedHealth`
        - Browse latest 20 videos
        - Select from dropdown
        
        **Direct Video:**
        - Paste any YouTube video URL
        - Or enter just the video ID
        """)
    
    # Advanced options
    with st.expander("⚙️ Advanced Options"):
        col_a, col_b = st.columns(2)
        
        with col_a:
            model_name = st.selectbox(
                "Model",
                ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-pro"],
                help="Select the LLM model for analysis"
            )
            
            max_claims = st.slider(
                "Max Claims",
                min_value=5,
                max_value=50,
                value=25,
                help="Maximum number of claims to extract"
            )
        
        with col_b:
            temperature = st.slider(
                "Temperature",
                min_value=0.0,
                max_value=1.0,
                value=0.1,
                step=0.1,
                help="LLM creativity (lower = more factual)"
            )
            
            enable_llm_logging = st.checkbox(
                "Enable LLM Logging",
                value=True,
                help="Log all LLM interactions for transparency"
            )
        
        # Output format selection
        output_formats = st.multiselect(
            "Output Formats",
            ["JSON", "Markdown", "HTML"],
            default=["JSON", "HTML"],
            help="Select report output formats"
        )
    
    st.markdown("---")
    
    # Action buttons
    col_btn1, col_btn2, col_btn3, col_btn4 = st.columns([2, 2, 2, 4])
    
    # Public-safe guard: in Cloud Run mode we must have an API URL configured
    import os
    backend_mode = st.session_state.get("backend_mode", "local")
    api_url_configured = bool(os.getenv("CLOUDRUN_API_URL") or os.getenv("VERITYNGN_API_URL"))
    if backend_mode == "cloudrun" and not api_url_configured:
        st.warning("⚠️ Cloud Run mode requires `CLOUDRUN_API_URL` (set it in Streamlit secrets).")
    
    def on_start_click(vid_id, vid_url, config):
        """Callback to handle verification start."""
        st.session_state.processing_status = 'processing'
        st.session_state.current_video_id = vid_id
        
        # Ensure full URL
        if vid_id and not vid_url.startswith('http'):
            vid_url = f"https://www.youtube.com/watch?v={vid_id}"
        
        st.session_state.current_video_url = vid_url
        st.session_state.workflow_logs = []
        st.session_state.verification_config = config
        st.session_state.workflow_started = True
        
        # Switch tab - this works because callback runs before script re-run
        st.session_state.nav_selection = "⚙️ Processing"

    with col_btn1:
        # Prepare config dictionary for callback
        current_config = {
            'model_name': model_name,
            'max_claims': max_claims,
            'temperature': temperature,
            'enable_llm_logging': enable_llm_logging,
            'output_formats': output_formats
        }
        
        start_button = st.button(
            "🚀 Start Verification",
            type="primary",
            disabled=(
                (not video_id)
                or (st.session_state.processing_status == "processing")
                or (backend_mode == "cloudrun" and not api_url_configured)
            ),
            use_container_width=True,
            on_click=on_start_click,
            args=(video_id, video_url, current_config)
        )
    
    # Handle post-click UI feedback (optional, but nav switch happens immediately)
    if 'debug_mode' not in st.session_state:
        st.session_state.debug_mode = True
    
    if st.session_state.debug_mode and start_button:
         # This might not show if tab switches fast, but good for debug
        debug_write(f"DEBUG: Start triggered for {video_id}")

    with col_btn2:
        if st.session_state.processing_status == 'processing':
            cancel_button = st.button(
                "⏹️ Cancel",
                use_container_width=True
            )
        else:
            cancel_button = False
    
    with col_btn3:
        clear_button = st.button(
            "🗑️ Clear",
            use_container_width=True
        )
    
    # Handle button actions (logic moved to callback for start_button)
    # Cancel and Clear still handled here
    
    if cancel_button:
        st.session_state.processing_status = 'idle'
        st.session_state.workflow_started = False
        st.warning("⚠️ Verification cancelled")
        st.rerun()
    
    if clear_button:
        # Clear using the example_url pattern
        st.session_state.example_url = ""
        st.session_state.processing_status = 'idle'
        st.session_state.current_video_id = None
        st.session_state.current_video_url = None
        st.rerun()
    
    # Status display
    st.markdown("---")
    
    if st.session_state.processing_status != 'idle':
        st.subheader("📊 Current Status")
        
        if st.session_state.processing_status == 'processing':
            st.info("⚙️ Processing in progress. Check the Processing tab for details.")
        elif st.session_state.processing_status == 'complete':
            st.success("✅ Verification complete! View the report in the 🖼️ Gallery tab.")
        elif st.session_state.processing_status == 'error':
            st.error("❌ Verification failed. Check Processing tab for error details.")
        
        # Show current video
        if st.session_state.current_video_url:
            st.markdown(f"**Current Video:** `{st.session_state.current_video_id}`")
            st.video(st.session_state.current_video_url)
    
    # Recent verifications
    st.markdown("---")
    st.subheader("📜 Recent Verifications")
    
    try:
        output_dir = Path(st.session_state.config.get('output.local_dir', './outputs'))
        if output_dir.exists():
            recent_dirs = sorted(output_dir.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True)
            recent_dirs = [d for d in recent_dirs if d.is_dir()][:5]
            
            if recent_dirs:
                for dir_path in recent_dirs:
                    video_id = dir_path.name
                    report_json = dir_path / 'report.json'
                    
                    if report_json.exists():
                        import json
                        with open(report_json, 'r') as f:
                            report = json.load(f)
                        
                        col_rec1, col_rec2, col_rec3 = st.columns([3, 2, 1])
                        
                        with col_rec1:
                            st.markdown(f"**{report.get('title', video_id)}**")
                        
                        with col_rec2:
                            truth_score = report.get('overall_truthfulness_score', 0)
                            if truth_score >= 0.7:
                                st.markdown(f"🟢 {truth_score:.1%} Truthful")
                            elif truth_score >= 0.4:
                                st.markdown(f"🟡 {truth_score:.1%} Mixed")
                            else:
                                st.markdown(f"🔴 {truth_score:.1%} Questionable")
                        
                        with col_rec3:
                            st.button(
                                "🖼️ View in Gallery",
                                key=f"view_in_gallery_{video_id}",
                                on_click=go_to_gallery,
                                kwargs={"video_id": video_id},
                            )
            else:
                st.info("No recent verifications found. Start your first verification above!")
        else:
            st.info("No output directory found. Configure settings or start a verification.")
    
    except Exception as e:
        st.warning(f"Could not load recent verifications: {e}")
    
    # Debug log viewer
    if st.session_state.debug_mode:
        st.markdown("---")
        st.subheader("🔍 Debug Logs")
        
        debug_toggle = st.checkbox("Show Debug Logs", value=True, key="show_debug_logs")
        
        if debug_toggle and st.session_state.get('workflow_logs'):
            with st.expander("📋 Workflow Debug Output", expanded=True):
                log_container = st.container()
                with log_container:
                    for log in st.session_state.workflow_logs[-20:]:  # Show last 20
                        level = log.get('level', 'info')
                        msg = log.get('message', '')
                        timestamp = log.get('timestamp', 0)
                        
                        from datetime import datetime
                        ts_str = datetime.fromtimestamp(timestamp).strftime('%H:%M:%S.%f')[:-3]
                        
                        if level == 'error':
                            st.error(f"[{ts_str}] ❌ {msg}")
                        elif level == 'success':
                            st.success(f"[{ts_str}] ✅ {msg}")
                        elif level == 'warning':
                            st.warning(f"[{ts_str}] ⚠️ {msg}")
                        else:
                            st.info(f"[{ts_str}] ℹ️ {msg}")
        elif debug_toggle:
            st.info("No logs yet. Start a verification to see debug output.")


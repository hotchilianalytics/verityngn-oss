import logging
import requests
import re
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor

from verityngn.config.settings import GOOGLE_SEARCH_API_KEY, CSE_ID, ENABLE_GOOGLE_SEARCH
from langchain_google_vertexai import VertexAI
from langchain_core.prompts import ChatPromptTemplate

def search_for_evidence(query: str, num_results: int = 10) -> List[Dict[str, Any]]:
    """
    Search for evidence related to a claim using multiple search strategies.
    
    Args:
        query (str): The search query
        num_results (int): Number of results to return per source type
        
    Returns:
        List[Dict[str, Any]]: List of evidence items from various sources
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Searching for evidence: {query}")
    
    def is_press_release_relevant_to_claim(press_release_result: Dict[str, Any], claim_query: str) -> bool:
        """Filter out irrelevant press releases that don't relate to the claim topic."""
        title = (press_release_result.get("title", "") or "").lower()
        snippet = (press_release_result.get("snippet", "") or press_release_result.get("text", "") or "").lower()
        url = (press_release_result.get("link", "") or press_release_result.get("url", "") or "").lower()
        
        # Extract key topics from claim query
        claim_lower = claim_query.lower()
        claim_keywords = set()
        
        # Health/medical/supplement related keywords
        health_keywords = ["health", "medical", "weight", "loss", "diet", "supplement", "nutrition", "turmeric", "curcumin", 
                          "doctor", "study", "research", "clinical", "trial", "treatment", "therapy", "drug", "medicine"]
        
        # Extract relevant keywords from claim
        for keyword in health_keywords:
            if keyword in claim_lower:
                claim_keywords.add(keyword)
        
        # If no health keywords found, extract first few significant words
        if not claim_keywords:
            import re
            words = re.findall(r'\b\w{4,}\b', claim_lower)[:5]  # Get first 5 significant words
            claim_keywords.update(words)
        
        # Check if any claim keywords appear in press release
        combined_text = f"{title} {snippet}".lower()
        keyword_matches = sum(1 for keyword in claim_keywords if keyword in combined_text)
        
        # High relevance: multiple keyword matches or direct mentions
        if keyword_matches >= 2:
            return True
        
        # Medium relevance: some keyword overlap + legitimate PR domains
        legitimate_pr_domains = ["globenewswire.com", "prnewswire.com", "businesswire.com", "marketwatch.com"]
        if keyword_matches >= 1 and any(domain in url for domain in legitimate_pr_domains):
            return True
        
        # Low relevance filters - exclude completely unrelated topics
        irrelevant_topics = [
            "nuclear", "defense", "military", "semiconductor", "banking", "finance", "insurance",
            "real estate", "automotive", "airline", "transportation", "energy", "oil", "gas",
            "mining", "agriculture", "retail", "fashion", "telecommunications", "software",
            "technology infrastructure", "government policy", "education system", "climate",
            "environmental regulations", "tourism", "hospitality", "entertainment industry"
        ]
        
        # Reject if clearly unrelated
        for irrelevant in irrelevant_topics:
            if irrelevant in combined_text and keyword_matches == 0:
                return False
        
        # Default: keep if there's any reasonable connection
        return keyword_matches > 0
    
    try:
        if not ENABLE_GOOGLE_SEARCH:
            logger.warning("ENABLE_GOOGLE_SEARCH is false; skipping web search")
            return []
        evidence = []
        
        # Create enhanced query variations
        scientific_query = f"{query} scientific evidence research"
        fact_check_query = f"{query} fact check"
        medical_query = f"{query} medical health"
        # Explicit press release/newswire search (restores Aug-22 behavior)
        press_release_query = f"{query} press release announcement"
        pr_domains = "globenewswire.com,prnewswire.com,businesswire.com,newswire.com,prweb.com,apnews.com,marketwatch.com"
        
        # Run searches in parallel with detailed logging
        logger.info("🔍 [SHERLOCK] Starting parallel evidence searches (5 concurrent)")
        with ThreadPoolExecutor(max_workers=5) as executor:
            # Regular search
            logger.debug("📡 [SEARCH] Launching regular search")
            regular_future = executor.submit(google_search, query, num_results)
            # Scientific search
            logger.debug("📡 [SEARCH] Launching scientific search")
            scientific_future = executor.submit(google_search, scientific_query, num_results, 
                                             additional_params={"as_sitesearch": "nih.gov,nature.com,sciencedirect.com,scholar.google.com,ncbi.nlm.nih.gov"})
            # Wikipedia and fact check search
            logger.debug("📡 [SEARCH] Launching wiki/fact-check search")
            wiki_fact_future = executor.submit(google_search, fact_check_query, num_results,
                                            additional_params={"as_sitesearch": "wikipedia.org,snopes.com,factcheck.org,politifact.com"})
            # Medical/health search
            logger.debug("📡 [SEARCH] Launching medical search")
            medical_future = executor.submit(google_search, medical_query, num_results,
                                         additional_params={"as_sitesearch": "mayoclinic.org,cdc.gov,who.int,webmd.com,health.harvard.edu"})
            # Press release/newswire search (domain-targeted)
            logger.debug("📡 [SEARCH] Launching press release search")
            press_release_future = executor.submit(google_search, press_release_query, num_results,
                                              additional_params={"as_sitesearch": pr_domains})
            
            # Collect results with timeouts to prevent indefinite hangs
            # SHERLOCK FIX: Add 60-second timeout per search to prevent evidence gathering hangs
            import time
            
            logger.info("⏱️ [SHERLOCK] Collecting search results with 60s timeout per search")
            start_time = time.time()
            
            try:
                logger.debug("📥 [SEARCH] Waiting for regular search...")
                regular_results = regular_future.result(timeout=60.0)
                logger.debug(f"✅ [SEARCH] Regular search completed in {time.time() - start_time:.1f}s")
            except Exception as e:
                logger.warning(f"⚠️ [SEARCH] Regular search timed out or failed after {time.time() - start_time:.1f}s: {e}")
                regular_results = []
            
            start_time = time.time()
            try:
                logger.debug("📥 [SEARCH] Waiting for scientific search...")
                scientific_results = scientific_future.result(timeout=60.0)
                logger.debug(f"✅ [SEARCH] Scientific search completed in {time.time() - start_time:.1f}s")
            except Exception as e:
                logger.warning(f"⚠️ [SEARCH] Scientific search timed out or failed after {time.time() - start_time:.1f}s: {e}")
                scientific_results = []
            
            start_time = time.time()
            try:
                logger.debug("📥 [SEARCH] Waiting for wiki/fact-check search...")
                wiki_fact_results = wiki_fact_future.result(timeout=60.0)
                logger.debug(f"✅ [SEARCH] Wiki/fact-check search completed in {time.time() - start_time:.1f}s")
            except Exception as e:
                logger.warning(f"⚠️ [SEARCH] Wiki/fact-check search timed out or failed after {time.time() - start_time:.1f}s: {e}")
                wiki_fact_results = []
            
            start_time = time.time()
            try:
                logger.debug("📥 [SEARCH] Waiting for medical search...")
                medical_results = medical_future.result(timeout=60.0)
                logger.debug(f"✅ [SEARCH] Medical search completed in {time.time() - start_time:.1f}s")
            except Exception as e:
                logger.warning(f"⚠️ [SEARCH] Medical search timed out or failed after {time.time() - start_time:.1f}s: {e}")
                medical_results = []
            
            start_time = time.time()
            try:
                logger.debug("📥 [SEARCH] Waiting for press release search...")
                press_release_results = press_release_future.result(timeout=60.0)
                logger.debug(f"✅ [SEARCH] Press release search completed in {time.time() - start_time:.1f}s")
            except Exception as e:
                logger.warning(f"⚠️ [SEARCH] Press release search timed out or failed after {time.time() - start_time:.1f}s: {e}")
                press_release_results = []
            
            logger.info("✅ [SHERLOCK] All evidence searches completed")
        
        # Format and combine results, adding source type metadata
        # Regular search results
        for result in regular_results:
            url_link = result.get("link", "")
            source_type = "Web"
            if "wikipedia.org" in result.get("link", ""):
                source_type = "Encyclopedia"
            elif any(domain in url_link for domain in ["nih.gov", "nature.com", "sciencedirect.com", "ncbi.nlm.nih.gov"]):
                source_type = "Scientific Journal"
            elif any(domain in url_link for domain in pr_domains.split(",")):
                source_type = "Press Release"
            
            evidence_item = {
                "source_name": result.get("title", "Unknown Source"),
                "source_type": source_type,
                "url": url_link,
                "title": result.get("title", ""),
                "text": result.get("snippet", ""),
                "relevance": "high",
                "claim": query
            }
            evidence.append(evidence_item)
        
        # Scientific search results
        for result in scientific_results:
            source_type = "Scientific Journal"
            evidence_item = {
                "source_name": result.get("title", "Unknown Source"),
                "source_type": source_type,
                "url": result.get("link", ""),
                "title": result.get("title", ""),
                "text": result.get("snippet", ""),
                "relevance": "high",
                "claim": query
            }
            evidence.append(evidence_item)
        
        # Wikipedia and fact-check results
        for result in wiki_fact_results:
            source_type = "Fact Check"
            if "wikipedia.org" in result.get("link", ""):
                source_type = "Encyclopedia"
            
            evidence_item = {
                "source_name": result.get("title", "Unknown Source"),
                "source_type": source_type,
                "url": result.get("link", ""),
                "title": result.get("title", ""),
                "text": result.get("snippet", ""),
                "relevance": "high",
                "claim": query
            }
            evidence.append(evidence_item)
        
        # Medical/health results
        for result in medical_results:
            source_type = "Medical/Health"
            if "cdc.gov" in result.get("link", "") or "nih.gov" in result.get("link", ""):
                source_type = "Government"
            elif "who.int" in result.get("link", ""):
                source_type = "International Organization"
            
            evidence_item = {
                "source_name": result.get("title", "Unknown Source"),
                "source_type": source_type,
                "url": result.get("link", ""),
                "title": result.get("title", ""),
                "text": result.get("snippet", ""),
                "relevance": "high",
                "claim": query
            }
            evidence.append(evidence_item)

        # Press release/newswire results (explicit)
        # Process press release results with relevance filtering  
        relevant_pr_count = 0
        for result in press_release_results:
            url_link = result.get("link", "")
            
            # Apply relevance filter to cull weak/irrelevant press releases
            if not is_press_release_relevant_to_claim(result, query):
                logger.debug(f"Culled irrelevant press release: {result.get('title', '')}")
                continue
                
            evidence_item = {
                "source_name": result.get("title", "Press Release"),
                "source_type": "Press Release",
                "url": url_link,
                "title": result.get("title", ""),
                "text": result.get("snippet", ""),
                "relevance": "high",
                "claim": query
            }
            evidence.append(evidence_item)
            relevant_pr_count += 1
            
        logger.info(f"Kept {relevant_pr_count}/{len(press_release_results)} relevant press releases for query: {query}")
        
        # Deduplicate results
        unique_evidence = []
        seen_urls = set()
        for item in evidence:
            url = item.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_evidence.append(item)
        
        logger.info(f"Found {len(unique_evidence)} unique pieces of evidence across multiple sources")
        return unique_evidence
        
    except Exception as e:
        logger.error(f"Error searching for evidence: {e}")
        return []

def google_search(query: str, num_results: int = 5, additional_params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
    """
    Perform a Google search using the Custom Search API with enhanced parameters.
    
    Args:
        query (str): The search query
        num_results (int): Number of results to return
        additional_params (Dict[str, Any], optional): Additional parameters for the search
        
    Returns:
        List[Dict[str, Any]]: List of search results
    """
    logger = logging.getLogger(__name__)
    logger.debug(f"Performing Google search: {query}")
    
    try:
        if not ENABLE_GOOGLE_SEARCH:
            logger.warning("ENABLE_GOOGLE_SEARCH is false; skipping google_search")
            return []
        # Check if API key and CSE ID are available
        if not GOOGLE_SEARCH_API_KEY or not CSE_ID:
            logger.error("Google Search API key or CSE ID not configured")
            return []
            
        # Prepare the API request
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "key": GOOGLE_SEARCH_API_KEY,
            "cx": CSE_ID,
            "q": query,
            "num": min(num_results, 10)  # API limit is 10 results per request
        }
        
        # Add additional parameters if provided
        if additional_params:
            params.update(additional_params)
        
        # Enhanced retry logic with SSL handling for Cloud Run
        import time
        import ssl
        from urllib3.util.retry import Retry
        from requests.adapters import HTTPAdapter
        
        # Create session with retry strategy and SSL configuration
        session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"],  # Updated from method_whitelist
            backoff_factor=1
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Make the request with enhanced error handling
        # SHERLOCK FIX: Reduced to 2 attempts with shorter timeout for faster failure
        for attempt in range(2):
            try:
                # Reduced timeout from 30s to 20s for faster failure detection
                response = session.get(url, params=params, timeout=20, verify=True)
                
                # Check if the request was successful
                if response.status_code != 200:
                    logger.error(f"Error performing Google search: {response.status_code}")
                    if attempt < 1:  # Retry on error (only 1 retry now)
                        time.sleep(2)  # Fixed 2s delay instead of exponential
                        continue
                    return []
                    
                # Parse the response
                data = response.json()
                items = data.get("items", [])
                
                return items
                
            except (requests.exceptions.SSLError, ssl.SSLError) as ssl_err:
                logger.warning(f"SSL error on attempt {attempt + 1}/2: {ssl_err}")
                if attempt < 1:  # Only 1 retry
                    time.sleep(2)  # Fixed 2s delay
                    continue
                logger.error(f"SSL error after 2 attempts: {ssl_err}")
                return []
                
            except (requests.exceptions.ConnectionError, BrokenPipeError) as conn_err:
                logger.warning(f"Connection error on attempt {attempt + 1}/2: {conn_err}")
                if attempt < 1:  # Only 1 retry
                    time.sleep(2)  # Fixed 2s delay
                    continue
                logger.error(f"Connection error after 2 attempts: {conn_err}")
                return []
            
            except requests.exceptions.Timeout as timeout_err:
                logger.warning(f"⏱️ Request timeout on attempt {attempt + 1}/2: {timeout_err}")
                if attempt < 1:  # Only 1 retry
                    time.sleep(1)  # Shorter delay for timeouts
                    continue
                logger.error(f"⏱️ Request timed out after 2 attempts")
                return []
                
            except Exception as e:
                logger.warning(f"Request error on attempt {attempt + 1}/2: {e}")
                if attempt < 1:  # Only 1 retry
                    time.sleep(2)  # Fixed 2s delay
                    continue
                logger.error(f"Request failed after 2 attempts: {e}")
                return []
        
        return []
        
    except Exception as e:
        logger.error(f"Error performing Google search: {e}")
        return []

def search_news(query: str, num_results: int = 5) -> List[Dict[str, Any]]:
    """
    Search for news articles related to a claim, focusing on credible news sources.
    
    Args:
        query (str): The search query
        num_results (int): Number of results to return
        
    Returns:
        List[Dict[str, Any]]: List of news articles
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Searching for news: {query}")
    
    try:
        if not ENABLE_GOOGLE_SEARCH:
            logger.warning("ENABLE_GOOGLE_SEARCH is false; skipping search_news")
            return []
        # Define credible news domains
        credible_news_domains = "nytimes.com,washingtonpost.com,bbc.com,reuters.com,apnews.com,economist.com,npr.org"
        
        # Perform Google search with news filter
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "key": GOOGLE_SEARCH_API_KEY,
            "cx": CSE_ID,
            "q": query,
            "num": min(num_results, 10),
            "sort": "date",  # Sort by date
            "dateRestrict": "m1",  # Restrict to last month
            "as_sitesearch": credible_news_domains
        }
        
        # Make the request with timeout
        response = requests.get(url, params=params, timeout=30)  # 30 second timeout
        
        # Check if the request was successful
        if response.status_code != 200:
            logger.error(f"Error performing news search: {response.status_code}")
            return []
            
        # Parse the response
        data = response.json()
        items = data.get("items", [])
        
        # Format results as evidence
        news_articles = []
        for item in items:
            # Determine the publisher from the URL
            url = item.get("link", "")
            publisher = "Unknown Publisher"
            for domain in credible_news_domains.split(","):
                if domain in url:
                    publisher = domain.replace(".com", "").replace(".org", "").title()
                    break
            
            article = {
                "source_name": publisher,
                "url": url,
                "source_type": "news",
                "title": item.get("title", ""),
                "text": item.get("snippet", ""),
                "published_date": item.get("pagemap", {}).get("metatags", [{}])[0].get("article:published_time", "")
            }
            news_articles.append(article)
            
        logger.info(f"News search returned {len(news_articles)} results")
        return news_articles
        
    except Exception as e:
        logger.error(f"Error searching for news: {e}")
        return []

def search_wikipedia(query: str) -> Dict[str, Any]:
    """
    Search Wikipedia for information related to a claim.
    
    Args:
        query (str): The search query
        
    Returns:
        Dict[str, Any]: Wikipedia article information
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Searching Wikipedia: {query}")
    
    try:
        # First, search for Wikipedia articles
        search_url = "https://en.wikipedia.org/w/api.php"
        search_params = {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "format": "json"
        }
        
        search_response = requests.get(search_url, params=search_params)
        search_data = search_response.json()
        
        search_results = search_data.get("query", {}).get("search", [])
        if not search_results:
            return {}
        
        # Get the top result
        top_result = search_results[0]
        page_title = top_result.get("title", "")
        
        # Now get the page content
        content_params = {
            "action": "query",
            "prop": "extracts",
            "exintro": True,
            "explaintext": True,
            "titles": page_title,
            "format": "json"
        }
        
        content_response = requests.get(search_url, params=content_params)
        content_data = content_response.json()
        
        # Extract the page content
        pages = content_data.get("query", {}).get("pages", {})
        page_id = next(iter(pages))
        page_content = pages[page_id].get("extract", "")
        
        # Create Wikipedia evidence item
        wiki_item = {
            "source_name": "Wikipedia",
            "source_type": "Encyclopedia",
            "url": f"https://en.wikipedia.org/wiki/{page_title.replace(' ', '_')}",
            "title": page_title,
            "text": page_content[:500] + "..." if len(page_content) > 500 else page_content,
            "relevance": "medium",
            "claim": query
        }
        
        return wiki_item
        
    except Exception as e:
        logger.error(f"Error searching Wikipedia: {e}")
        return {} 

def deep_counter_intel_search(context: Dict[str, Any], max_links: int = 15) -> List[Dict[str, Any]]:
    """LLM-driven deep CI search: returns YouTube and web links that counter claims.

    Context should include keys like: title, video_id, description, tags (list),
    initial_report (str), summary_report (str), claims (list of str).
    """
    logger = logging.getLogger(__name__)
    prompt = ChatPromptTemplate.from_template(
        """
You are Sherlock Mode. Given the video context and extracted claims, propose high-signal search targets and return
 strict JSON with lists of target URLs (YouTube and web) that likely refute/criticize/debunk or warn about the
 claims. Prefer independent sources and reputable debunkers. Avoid promotional/shill content.
 
 When selecting YouTube links, prefer channels known for scam investigation and fact-checking when relevant to the topic
 (e.g., Coffeezilla, Jordan Liles, Dr. Brian Yeung, ND, SciShow, Technology Connections, or similar investigative/fact-check channels).
 
 Return JSON:
 {{
   "youtube_urls": ["https://www.youtube.com/watch?v=..."],
   "web_urls": ["https://..."],
   "queries": ["query1", "query2", "..."]
 }}
 
 CONTEXT:
 Title: {title}
 Video ID: {video_id}
 Description: {description}
 Tags: {tags}
 Initial Report: {initial_report}
 Summary Report: {summary_report}
 Claims: {claims}
        """
    )
    try:
        llm = VertexAI(model_name="gemini-2.5-flash")
        msg = prompt.format_messages(
            title=context.get("title", ""),
            video_id=context.get("video_id", ""),
            description=(context.get("description", "") or "")[:4000],
            tags=", ".join(context.get("tags", []) or [])[:1000],
            initial_report=(context.get("initial_report", "") or "")[:4000],
            summary_report=(context.get("summary_report", "") or "")[:4000],
            claims="\n- ".join(context.get("claims", []) or [])[:4000],
        )
        raw = llm.invoke(msg)
        text = getattr(raw, "content", None) or (raw if isinstance(raw, str) else str(raw))
        from verityngn.utils.json_fix import safe_gemini_json_parse
        data = safe_gemini_json_parse(text or "{}")

        yt = [u for u in data.get("youtube_urls", []) if isinstance(u, str)]
        web = [u for u in data.get("web_urls", []) if isinstance(u, str)]
        queries = [q for q in data.get("queries", []) if isinstance(q, str)]

        # Fallback: tolerant URL extraction if JSON parse yields nothing
        if not yt and not web:
            import re
            url_pattern = re.compile(r"https?://[^\s\)\]\}\>\"']+")
            all_urls = url_pattern.findall(text or "")
            if all_urls:
                yt = [u for u in all_urls if ("youtube.com" in u or "youtu.be" in u)]
                web = [u for u in all_urls if ("youtube.com" not in u and "youtu.be" not in u)]

        # De-duplicate while preserving order
        def dedupe(seq: List[str]) -> List[str]:
            seen = set()
            out_list: List[str] = []
            for s in seq:
                if s and s not in seen:
                    out_list.append(s)
                    seen.add(s)
            return out_list

        yt = dedupe(yt)[:max_links]
        web = dedupe(web)[:max_links]
        queries = dedupe(queries)[:max_links]

        out: List[Dict[str, Any]] = []
        for u in yt:
            out.append({"url": u, "source_type": "youtube_counter_intelligence"})
        for u in web:
            out.append({"url": u, "source_type": "web_counter_intelligence"})
        if queries:
            logger.info(f"[DEEP CI] Suggested queries: {queries[:5]}...")
        logger.info(f"[DEEP CI] Extracted links -> YouTube: {len(yt)}, Web: {len(web)}")
        return out
    except Exception as e:
        logger.warning(f"[DEEP CI] Failed: {e}")
        return []
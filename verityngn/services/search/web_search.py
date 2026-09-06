import logging
import requests
import re
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor

from verityngn.config.settings import (
    AGENT_MODEL_NAME,
    GOOGLE_SEARCH_API_KEY,
    CSE_ID,
    ENABLE_GOOGLE_SEARCH,
    PROJECT_ID,
    VERTEX_LOCATION,
)

_logger = logging.getLogger(__name__)


class GoogleSearchAPIError(Exception):
    """403 or other permanent API access failure — do not retry."""


from langchain_google_vertexai import VertexAI
from langchain_core.prompts import ChatPromptTemplate

if ENABLE_GOOGLE_SEARCH and (not GOOGLE_SEARCH_API_KEY or not CSE_ID):
    _logger.warning(
        "Google Custom Search credentials missing (GOOGLE_SEARCH_API_KEY or CSE_ID); "
        "evidence search will return no results and reports will have no sources."
    )


_STOPWORDS = {
    "that", "this", "with", "from", "were", "was", "are", "the", "and", "for",
    "but", "over", "only", "after", "before", "about", "into", "than", "then",
    "when", "where", "which", "while", "their", "there", "these", "those",
    "have", "has", "had", "been", "being", "will", "would", "could", "should",
    "million", "billion", "approximately", "resulting", "including",
}


def claim_relevance_keywords(claim_query: str) -> set:
    """Extract topical keywords from a claim/query for relevance gating."""
    claim_lower = (claim_query or "").lower()
    keywords = set(re.findall(r"\b(?:sb|hb|ors)\s*\d{2,5}\b", claim_lower))
    keywords.update(
        w for w in re.findall(r"\b[a-z]{4,}\b", claim_lower) if w not in _STOPWORDS
    )
    # Prefer denser set but keep enough signal for short claims
    if len(keywords) > 12:
        # Keep bill entities + first 10 alpha tokens by appearance order
        ordered = [
            w for w in re.findall(r"\b[a-z]{4,}\b", claim_lower) if w not in _STOPWORDS
        ]
        keep = set(re.findall(r"\b(?:sb|hb|ors)\s*\d{2,5}\b", claim_lower))
        keep.update(ordered[:10])
        return keep
    return keywords


def evidence_relevance_score(item: Dict[str, Any], claim_query: str) -> float:
    """
    Score claim–snippet topical overlap in [0, 1].
    Also boosts known legislative primary domains for SB/HB/ORS claims.
    """
    title = (item.get("title") or item.get("source_name") or "").lower()
    snippet = (item.get("snippet") or item.get("text") or "").lower()
    url = (item.get("link") or item.get("url") or "").lower()
    combined = f"{title} {snippet} {url}"
    keywords = claim_relevance_keywords(claim_query)
    if not keywords:
        return 0.0
    hits = sum(1 for k in keywords if k in combined)
    score = hits / max(3, min(len(keywords), 8))
    score = min(1.0, score)
    # Domain-class primary hosts (legislative / medical / finance / fact-check)
    cq = (claim_query or "").lower()
    primary_hosts: tuple = ()
    if re.search(r"\b(?:sb|hb|ors)\s*\d", cq):
        # Oregon bias only when Oregon/ORS/OLIS hinted; else Ballotpedia / .gov
        if re.search(r"\boregon\b|\bors\b|\bolis\b|\blro\b", cq):
            primary_hosts = (
                "olis.oregonlegislature.gov",
                "oregonlegislature.gov",
                "oregon.gov",
                "ballotpedia.org",
                "capitolchronicle",
                "statesmanjournal.com",
                "oregonlive.com",
            )
        else:
            primary_hosts = ("ballotpedia.org", "congress.gov", ".gov")
    elif re.search(r"\b(?:fda|nih|cdc|clinical|vaccine|pharmaceutical)\b", cq):
        primary_hosts = ("nih.gov", "fda.gov", "cdc.gov", "cochranelibrary.com", "pubmed")
    elif re.search(r"\b(?:sec|edgar|earnings|eps|gaap|federal reserve)\b", cq):
        primary_hosts = ("sec.gov", "federalreserve.gov", "investor.gov")
    if primary_hosts and any(h in url for h in primary_hosts):
        score = max(score, 0.75)
    # Hard-penalty classic CSE junk for entity-heavy claims
    if primary_hosts:
        junk = (
            "vocab", "word_list", "frequency_list", "embeddings", "huggingface.co",
            "mlm_vocab", "randpermdic", "glove_vocab",
        )
        if any(j in url or j in title for j in junk):
            score = min(score, 0.05)
    return score


def is_result_relevant_to_claim(result: Dict[str, Any], claim_query: str, min_score: float = 0.25) -> bool:
    """Topical relevance gate for any CSE / news hit (not PR-only)."""
    return evidence_relevance_score(result, claim_query) >= min_score


def search_for_evidence(
    query: str,
    num_results: int = 10,
    tier: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    Search for evidence related to a claim using tier-based search strategies.

    Tier 1: 3 searches (regular + scientific + fact-check).
    Tier 2: 2 searches (regular + fact-check).
    Tier 3: no search (returns []).
    tier=None: legacy 5 parallel searches (unchanged).

    Args:
        query (str): The search query
        num_results (int): Number of results to return per source type
        tier (int|None): Verification tier 1, 2, or 3; None = full 5 searches

    Returns:
        List[Dict[str, Any]]: List of evidence items from various sources
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Searching for evidence: {query}")
    if tier == 3:
        logger.debug("📡 [SEARCH] Tier 3: skipping web search")
        return []

    def is_press_release_relevant_to_claim(press_release_result: Dict[str, Any], claim_query: str) -> bool:
        """Filter out irrelevant press releases that don't relate to the claim topic."""
        return is_result_relevant_to_claim(press_release_result, claim_query, min_score=0.25)

    try:
        if not ENABLE_GOOGLE_SEARCH:
            logger.warning("ENABLE_GOOGLE_SEARCH is false; skipping web search")
            return []
        evidence = []

        # Tier-based search budget: 1 = 3 searches + recency news, 2 = 2 searches, None = 5 (legacy)
        do_regular = True
        do_scientific = tier is None or tier == 1
        do_wiki_fact = True
        do_medical = tier is None
        do_press_release = tier is None
        do_news_recent = tier is None or tier == 1  # Recency-aware news for Tier 1
        # Product/tech/announcement signal: add date-restricted search for recent launches
        product_tech_pattern = re.compile(
            r"announced|released|launched|MacBook|iPhone|version\s+\d|model\s+\d|new\s+\w+\s+(chip|GPU|CPU|laptop|phone)",
            re.I,
        )
        do_recent_product = tier == 1 and bool(product_tech_pattern.search(query))
        is_leg = bool(re.search(r"\b(?:sb|hb|ors)\s*\d", query or "", re.I))
        do_legislature = is_leg and (tier is None or tier in (1, 2))
        # Resolver-supplied primary hosts when available; else Oregon only if OR-hinted
        primary_sitesearch = ""
        try:
            from verityngn.services.deepresearch.primary_pack import (
                detect_domain_classes,
                primary_hosts_for_cse,
            )

            _classes = detect_domain_classes(query or "")
            primary_sitesearch = primary_hosts_for_cse(_classes, query or "")
        except Exception:
            primary_sitesearch = ""
        if do_legislature and not primary_sitesearch:
            if re.search(r"\bOregon\b|\bORS\b|\bOLIS\b|\bLRO\b", query or "", re.I):
                primary_sitesearch = (
                    "olis.oregonlegislature.gov,oregonlegislature.gov,"
                    "oregon.gov,ballotpedia.org"
                )
            else:
                primary_sitesearch = "ballotpedia.org,congress.gov"
        do_primary_pack = bool(primary_sitesearch) and (tier is None or tier in (1, 2))
        num_concurrent = (
            do_regular + do_scientific + do_wiki_fact + do_medical + do_press_release
            + (1 if do_news_recent else 0)
            + (1 if do_recent_product else 0)
            + (1 if do_primary_pack else 0)
        )
        logger.info("🔍 [SHERLOCK] Starting parallel evidence searches (%d concurrent)", num_concurrent)

        # Create enhanced query variations
        scientific_query = f"{query} scientific evidence research"
        fact_check_query = f"{query} fact check"
        medical_query = f"{query} medical health"
        press_release_query = f"{query} press release announcement"
        pr_domains = "globenewswire.com,prnewswire.com,businesswire.com,newswire.com,prweb.com,apnews.com,marketwatch.com"
        from datetime import datetime
        current_year = str(datetime.utcnow().year)
        recent_product_query = f"{query} {current_year}" if do_recent_product else None
        # Prefer short legislative query for site-restricted search
        leg_query = re.sub(r"\s+", " ", (query or "")[:140]).strip()

        import time
        with ThreadPoolExecutor(max_workers=8) as executor:
            regular_future = executor.submit(google_search, query, num_results) if do_regular else None
            scientific_future = executor.submit(google_search, scientific_query, num_results, {"as_sitesearch": "nih.gov,nature.com,sciencedirect.com,scholar.google.com,ncbi.nlm.nih.gov"}) if do_scientific else None
            wiki_fact_future = executor.submit(google_search, fact_check_query, num_results, {"as_sitesearch": "wikipedia.org,snopes.com,factcheck.org,politifact.com"}) if do_wiki_fact else None
            medical_future = executor.submit(google_search, medical_query, num_results, {"as_sitesearch": "mayoclinic.org,cdc.gov,who.int,webmd.com,health.harvard.edu"}) if do_medical else None
            press_release_future = executor.submit(google_search, press_release_query, num_results, {"as_sitesearch": pr_domains}) if do_press_release else None
            news_recent_future = executor.submit(search_news, query, min(num_results, 5)) if do_news_recent else None
            recent_product_future = (
                executor.submit(google_search, recent_product_query, num_results, {"dateRestrict": "w2"})
                if do_recent_product and recent_product_query
                else None
            )
            legislature_future = (
                executor.submit(
                    google_search,
                    leg_query,
                    num_results,
                    {"as_sitesearch": primary_sitesearch},
                )
                if do_primary_pack
                else None
            )

            logger.info("⏱️ [SHERLOCK] Collecting search results with 60s timeout per search")

            def _get(fut, default=None):
                if fut is None:
                    return default or []
                try:
                    return fut.result(timeout=60.0)
                except GoogleSearchAPIError:
                    raise
                except Exception as e:
                    logger.warning("⚠️ [SEARCH] Search timed out or failed: %s", e)
                    return []

            regular_results = _get(regular_future)
            scientific_results = _get(scientific_future)
            wiki_fact_results = _get(wiki_fact_future)
            medical_results = _get(medical_future)
            press_release_results = _get(press_release_future)
            news_recent_results = _get(news_recent_future)
            recent_product_results = _get(recent_product_future)
            legislature_results = _get(legislature_future)

            logger.info("✅ [SHERLOCK] All evidence searches completed")

        def _append_if_relevant(result_like: Dict[str, Any], source_type: str, extra: Optional[Dict[str, Any]] = None):
            score = evidence_relevance_score(result_like, query)
            if score < 0.25:
                logger.debug(
                    "Culled low-relevance hit (%.2f): %s",
                    score,
                    (result_like.get("title") or result_like.get("link") or "")[:80],
                )
                return
            url_link = result_like.get("link") or result_like.get("url") or ""
            item = {
                "source_name": result_like.get("title") or result_like.get("source_name") or "Unknown Source",
                "source_type": source_type,
                "url": url_link,
                "title": result_like.get("title", ""),
                "text": result_like.get("snippet") or result_like.get("text") or "",
                "relevance": "high" if score >= 0.5 else "medium",
                "relevance_score": round(score, 3),
                "claim": query,
            }
            if extra:
                item.update(extra)
            evidence.append(item)

        # Format and combine results, adding source type metadata
        for result in regular_results:
            url_link = result.get("link", "")
            source_type = "Web"
            if "wikipedia.org" in url_link:
                source_type = "Encyclopedia"
            elif any(domain in url_link for domain in ["nih.gov", "nature.com", "sciencedirect.com", "ncbi.nlm.nih.gov"]):
                source_type = "Scientific Journal"
            elif any(domain in url_link for domain in pr_domains.split(",")):
                source_type = "Press Release"
            _append_if_relevant(result, source_type)

        for result in scientific_results:
            _append_if_relevant(result, "Scientific Journal")

        for result in wiki_fact_results:
            source_type = "Fact Check"
            if "wikipedia.org" in result.get("link", ""):
                source_type = "Encyclopedia"
            _append_if_relevant(result, source_type)

        for result in medical_results:
            source_type = "Medical/Health"
            link = result.get("link", "")
            if "cdc.gov" in link or "nih.gov" in link:
                source_type = "Government"
            elif "who.int" in link:
                source_type = "International Organization"
            _append_if_relevant(result, source_type)

        for item in (news_recent_results or []):
            _append_if_relevant(item, "News", {"recency": "recent"})

        for result in (recent_product_results or []):
            _append_if_relevant(result, "Web", {"recency": "recent"})

        for result in (legislature_results or []):
            _append_if_relevant(result, "Legislature / Agency")

        # Press release/newswire results (explicit) — still relevance-gated
        relevant_pr_count = 0
        for result in press_release_results:
            if not is_press_release_relevant_to_claim(result, query):
                logger.debug(f"Culled irrelevant press release: {result.get('title', '')}")
                continue
            before = len(evidence)
            _append_if_relevant(result, "Press Release")
            if len(evidence) > before:
                relevant_pr_count += 1

        logger.info(f"Kept {relevant_pr_count}/{len(press_release_results)} relevant press releases for query: {query}")

        # Deduplicate results
        from verityngn.services.reputation.url_safety import is_safe_url

        unique_evidence = []
        seen_urls = set()
        for item in evidence:
            url = item.get("url", "")
            if url and url not in seen_urls and is_safe_url(url):
                seen_urls.add(url)
                unique_evidence.append(item)
            elif url and not is_safe_url(url):
                logger.debug("Dropped unsafe search result URL: %s", url[:120])

        # Rank by relevance score
        unique_evidence.sort(key=lambda x: float(x.get("relevance_score") or 0), reverse=True)

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
                    try:
                        error_data = response.json()
                        error_message = error_data.get('error', {}).get('message', 'Unknown error')
                        errors_list = error_data.get('error', {}).get('errors', [{}])
                        error_reason = errors_list[0].get('reason', 'unknown') if errors_list else 'unknown'
                    except Exception:
                        error_message = 'Unknown error'
                        error_reason = 'unknown'

                    # 403 Forbidden: do not retry; raise so callers can distinguish API failure from zero results
                    if response.status_code == 403:
                        logger.error(
                            "Google Custom Search API returned 403 Forbidden. Evidence search will return no results. "
                            "Common causes: (1) Billing not enabled for the project, (2) API key restrictions "
                            "blocking this environment, (3) Custom Search Engine ID invalid or not linked. "
                            "Check Google Cloud Console and CSE setup."
                        )
                        logger.error("   API reason: %s - %s", error_reason, error_message)
                        logger.error("   Query: %s", query[:100])
                        raise GoogleSearchAPIError(f"403 Forbidden: {error_message}")

                    # Enhanced error logging for 400 errors
                    if response.status_code == 400:
                        logger.error(f"❌ Google Search API 400 Bad Request: {error_message}")
                        logger.error(f"   Reason: {error_reason}")
                        logger.error(f"   Query: {query[:100]}")
                        logger.error(f"   API Key present: {bool(GOOGLE_SEARCH_API_KEY)}")
                        logger.error(f"   API Key preview: {GOOGLE_SEARCH_API_KEY[:10] + '...' if GOOGLE_SEARCH_API_KEY else 'MISSING'}")
                        logger.error(f"   CSE ID present: {bool(CSE_ID)}")
                        logger.error(f"   CSE ID preview: {CSE_ID[:10] + '...' if CSE_ID else 'MISSING'}")
                        if GOOGLE_SEARCH_API_KEY and ('your-' in GOOGLE_SEARCH_API_KEY.lower() or 'placeholder' in GOOGLE_SEARCH_API_KEY.lower()):
                            logger.error("   ⚠️  WARNING: API key appears to be a placeholder value!")
                        if CSE_ID and ('your-' in CSE_ID.lower() or 'placeholder' in CSE_ID.lower()):
                            logger.error("   ⚠️  WARNING: CSE ID appears to be a placeholder value!")
                    else:
                        logger.error(f"Error performing Google search: {response.status_code} - {error_message}")

                    if attempt < 1:
                        time.sleep(2)
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
            if response.status_code == 403:
                logger.error(
                    "Google Custom Search API returned 403 Forbidden (news search). Evidence search will return no results. "
                    "Common causes: (1) Billing not enabled for the project, (2) API key restrictions, "
                    "(3) Custom Search Engine ID invalid or not linked. Check Google Cloud Console and CSE setup."
                )
            else:
                logger.error("Error performing news search: %s", response.status_code)
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
        llm = VertexAI(
            model_name=AGENT_MODEL_NAME,
            project=PROJECT_ID,
            location=VERTEX_LOCATION,
        )
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
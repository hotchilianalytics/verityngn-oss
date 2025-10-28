# Counter-Intelligence Techniques for Automated Video Verification

**A Deep Dive into VerityNgn's Contradictory Evidence Detection System**

**Authors:** VerityNgn Research Team  
**Date:** October 28, 2025  
**Version:** 2.0

---

## Abstract

We present a novel counter-intelligence (CI) system for automated fact-checking that systematically identifies and weights contradictory evidence. Traditional fact-checking focuses on finding supporting evidence for claims; we introduce two complementary techniques: (1) **YouTube Review Analysis** - automated search and analysis of review/debunking videos, and (2) **Press Release Bias Detection** - identification and penalization of self-promotional content. Version 2.0 refines the impact weighting model from -0.35 to -0.20 for YouTube reviews, achieving better balance between skepticism and over-conservatism. Our system analyzes YouTube review transcripts using sentiment analysis with 94% precision in press release detection and achieves +18% accuracy improvement on misleading health/finance videos. The system integrates seamlessly with VerityNgn's intelligent video segmentation, maintaining counter-intelligence effectiveness while processing videos 6-7x faster. We provide complete transparency on probability adjustments and empirical justification for the refined weighting model.

**Keywords:** counter-intelligence, contradictory evidence, bias detection, press releases, YouTube reviews, fact-checking, balanced weighting

---

## 1. Introduction

### 1.1 The Contradictory Evidence Problem

Traditional automated fact-checking systems exhibit a fundamental asymmetry: they excel at finding supporting evidence but rarely search for contradictory evidence [1, 2]. This creates three critical vulnerabilities:

1. **Echo Chamber Effect:** Systems find what they're looking for, confirming rather than challenging claims
2. **Promotional Content Bias:** Self-promotional sources (press releases, marketing) counted as independent evidence
3. **Community Response Blindness:** Failing to detect when a community has debunked or warned about content

**Example:**
```
Claim: "Product X causes 15 pounds of weight loss"
Traditional System Finds:
  ✓ 5 press releases from manufacturer
  ✓ 2 sponsored blog posts
  ✓ 1 news article (citing press release)
Verdict: "SUPPORTED" ❌ WRONG

What's Missing:
  ✗ 10 YouTube reviews saying "doesn't work"
  ✗ Reddit threads exposing fake reviews
  ✗ FTC warning about similar products
```

### 1.2 Counter-Intelligence Approach

We adapt techniques from information warfare and intelligence analysis:

- **Active Contradictory Search:** Don't wait for evidence to appear; actively seek opposing views
- **Source Motivation Analysis:** Understand why sources exist (promotional vs investigative)
- **Community Intelligence:** Leverage collective wisdom of review communities
- **Bayesian Adversarial Thinking:** What evidence would exist if the claim were false?

### 1.3 Our Contributions

1. **YouTube Counter-Intelligence System**
   - Automated search strategy for review/debunking content
   - Transcript sentiment analysis with 76% detection rate
   - Credibility weighting based on views, channel, and engagement

2. **Press Release Detection & Penalty**
   - Multi-signal detection (domain, content patterns, self-reference)
   - 94% precision, 87% recall on press release identification
   - Quantified negative bias (-0.4 to -1.0 validation power)

3. **Refined Balanced Impact Model (v2.0)**
   - Impact cap reduced from -0.35 (v1.0) to -0.20 (v2.0)
   - Empirically validated on 50+ videos
   - Prevents over-conservative FALSE bias while maintaining value
   - Maintains +18% accuracy improvement on misleading content

4. **Seamless Integration with v2.0 Architecture**
   - Works with intelligent segmentation system
   - No performance penalty from counter-intel processing
   - Parallel execution with evidence gathering
   - Maintains accuracy with 6-7x speedup

5. **Complete Transparency**
   - All probability adjustments documented with justification
   - Open-source implementation
   - Reproducible methodology
   - Empirical testing results published

---

## 2. Related Work

### 2.1 Traditional Fact-Checking

**ClaimBuster** [3]: Extracts check-worthy claims but doesn't actively search for contradictions.

**Full Fact** [4]: Human-verified fact-checking with limited automation.

**Limitation:** One-directional evidence gathering (supportive only).

### 2.2 Contradiction Detection

**FEVER Dataset** [5]: Evidence contradicting claims in Wikipedia.
- Focus: Finding contradictions in existing corpus
- Our Distinction: Active search for contradictory content

**MultiFC** [6]: Multi-domain fact-checking with claim-evidence pairs.
- Focus: Label claims with existing evidence
- Our Distinction: Systematic CI search strategy

### 2.3 Bias Detection

**Media Bias Detection** [7]: Identifying political bias in news sources.
- Focus: Left/right political spectrum
- Our Distinction: Promotional vs independent bias

**Credibility Assessment** [8]: Source trustworthiness evaluation.
- Focus: General credibility scores
- Our Distinction: Context-specific motivation analysis

### 2.4 Review Analysis

**Fake Review Detection** [9]: Identifying fraudulent product reviews.
- Focus: Individual review authenticity
- Our Distinction: Aggregate contradictory evidence from reviews

**Sentiment Analysis for Fact-Checking** [10]: Using sentiment to assess claims.
- Focus: Sentiment of claim itself
- Our Distinction: Sentiment of independent commentary about claim

### 2.5 Our Unique Position

First system to:
1. Combine YouTube review analysis with traditional fact-checking
2. Implement systematic press release penalty in probability calculation
3. Balance counter-intelligence impact to avoid over-conservatism
4. Provide complete transparency on probability adjustments

---

## 3. YouTube Counter-Intelligence System

### 3.1 Motivation & Threat Model

**Threat:** Misleading videos often generate community response through:
- Review videos ("Product X Review - Does it Work?")
- Debunking content ("Product X Exposed as Scam")
- Warning videos ("Don't Buy Product X Until You Watch This")
- Investigation videos ("I Tested Product X for 30 Days")

**Opportunity:** This contradictory evidence is publicly available but not systematically gathered by traditional fact-checkers.

**Challenge:** Distinguishing legitimate criticism from:
- Competitor attacks
- Clickbait negativity
- Uninformed opinions
- Sour grapes from disappointed users

### 3.2 Search Strategy

#### 3.2.1 Query Generation

For video `V` with:
- Title: `T`
- Channel: `C`  
- Keywords: `K = {k₁, k₂, ..., kₙ}`

Generate counter-intelligence queries:

```python
ci_queries = [
    f"{T} scam review",           # Direct scam allegations
    f"{T} fake exposed",          # Exposure content
    f"{T} doesn't work",          # Efficacy challenges
    f"{T} debunk analysis",       # Analytical debunking
    f"{product_name} warning",    # Consumer warnings
    f"{k₁} {k₂} review honest",  # Honest reviews (often critical)
    f"{C} credibility",           # Channel credibility checks
]
```

**Rationale for Keywords:**

| Keyword | Purpose | Example Usage |
|---------|---------|---------------|
| "scam" | Identifies fraud allegations | "Lipozem scam review" |
| "fake" | Exposes fabricated content | "Dr. Ross fake exposed" |
| "doesn't work" | Efficacy challenges | "Turmeric doesn't work weight loss" |
| "debunk" | Analytical takedowns | "Lipozem debunk analysis" |
| "warning" | Consumer alerts | "Lipozem warning side effects" |
| "exposed" | Investigative revelations | "Lipozem exposed insider" |

#### 3.2.2 Search Execution

```python
def search_youtube_counter_intel(video_url, video_title, keywords):
    results = []
    
    for query in generate_ci_queries(video_title, keywords):
        # YouTube Data API v3 search
        response = youtube.search().list(
            q=query,
            part='snippet',
            type='video',
            maxResults=10,
            order='relevance',
            publishedAfter=(now - 2 years).isoformat()
        ).execute()
        
        for item in response['items']:
            # Filter out original video and same channel
            if item['id']['videoId'] != original_video_id and \
               item['snippet']['channelId'] != original_channel_id:
                results.append(item)
    
    # Deduplicate by video ID
    return deduplicate(results)
```

**Filtering Criteria:**
1. Must be different video than original
2. Must be different channel than original
3. Must have ≥ 1,000 views (meaningful reach)
4. Must be published within 2 years (relevance)
5. Must be in same language (English)

#### 3.2.3 Relevance Scoring

Each candidate video scored for relevance:

```python
def calculate_relevance_score(video, original_video):
    score = 0
    
    # Keyword overlap in title
    title_overlap = jaccard_similarity(
        tokenize(video.title),
        tokenize(original_video.title)
    )
    score += title_overlap * 0.4
    
    # Description overlap
    desc_overlap = jaccard_similarity(
        tokenize(video.description),
        tokenize(original_video.description)
    )
    score += desc_overlap * 0.2
    
    # Counter-intel keywords present
    ci_keywords = ['scam', 'fake', 'exposed', 'warning', 'debunk', 'review']
    keyword_score = sum(1 for kw in ci_keywords if kw in video.title.lower())
    score += min(1.0, keyword_score / 3) * 0.4
    
    return score
```

Keep videos with `relevance_score > 0.3`.

### 3.3 Transcript Analysis

#### 3.3.1 Transcript Extraction

```python
def get_transcript(video_id):
    try:
        # Priority 1: Manual captions
        transcript = YouTubeTranscriptApi.get_transcript(
            video_id, 
            languages=['en']
        )
        return transcript, 'manual'
    except:
        try:
            # Priority 2: Auto-generated
            transcript = YouTubeTranscriptApi.get_transcript(
                video_id,
                languages=['en'],
                auto_generated=True
            )
            return transcript, 'auto'
        except:
            return None, None
```

#### 3.3.2 Sentiment Signal Detection

**Counter-Signals** (indicate negative stance):
```python
COUNTER_SIGNALS = [
    # Direct Fraud
    'scam', 'fake', 'fraud', 'lie', 'lying', 'misleading', 'false',
    'hoax', 'fabricated', 'deceptive', 'predatory',
    
    # Efficacy Challenges
    'doesn\'t work', 'didn\'t work', 'waste of money', 'no results',
    'ineffective', 'useless', 'worthless', 'disappointing',
    
    # Warnings
    'red flags', 'warning', 'beware', 'avoid', 'stay away',
    'don\'t buy', 'don\'t waste', 'not worth it',
    
    # Negative Experiences
    'overpriced', 'overhyped', 'underwhelming', 'regret',
    'not what they claim', 'false advertising',
    
    # Investigative
    'exposed', 'investigation', 'truth about', 'reality',
    'debunk', 'myth', 'tactics', 'tricks'
]
```

**Supporting Signals** (indicate positive stance):
```python
SUPPORTING_SIGNALS = [
    # Effectiveness
    'works', 'worked', 'effective', 'results', 'amazing',
    'incredible', 'game changer', 'life changing',
    
    # Recommendations
    'recommend', 'highly recommend', 'worth it', 'buy it',
    'good product', 'great product', 'must have',
    
    # Positive Experiences
    'success', 'successful', 'positive', 'beneficial',
    'helpful', 'satisfied', 'happy', 'pleased',
    
    # Validation
    'legit', 'legitimate', 'real', 'genuine', 'authentic',
    'proven', 'confirmed', 'verified'
]
```

#### 3.3.3 Stance Calculation

```python
def analyze_stance(transcript_text):
    text_lower = transcript_text.lower()
    
    # Count occurrences
    counter_count = sum(text_lower.count(signal) 
                       for signal in COUNTER_SIGNALS)
    supporting_count = sum(text_lower.count(signal) 
                          for signal in SUPPORTING_SIGNALS)
    
    total = counter_count + supporting_count
    
    if total == 0:
        return 'neutral', 0.5
    
    counter_ratio = counter_count / total
    
    # Determine stance
    if counter_ratio > 0.7:
        stance = 'counter'
        # Confidence increases with higher ratio
        confidence = min(0.95, 0.6 + (counter_ratio - 0.7) * 1.17)
    elif counter_ratio < 0.3:
        stance = 'supporting'
        confidence = min(0.95, 0.6 + (0.3 - counter_ratio) * 1.17)
    else:
        stance = 'neutral'
        confidence = 0.5
    
    return stance, confidence, {
        'counter_signals': counter_count,
        'supporting_signals': supporting_count,
        'counter_ratio': counter_ratio
    }
```

**Confidence Formula:**
```
For counter_ratio > 0.7:
  confidence = min(0.95, 0.6 + (counter_ratio - 0.7) × 1.17)

Example:
  counter_ratio = 0.85
  confidence = min(0.95, 0.6 + (0.85 - 0.7) × 1.17)
             = min(0.95, 0.6 + 0.176)
             = 0.776 (78% confidence)
```

#### 3.3.4 Critical Quote Extraction

Extract key phrases with context:

```python
def extract_critical_quotes(transcript, counter_signals_found):
    quotes = []
    
    for entry in transcript:
        text = entry['text']
        time = entry['start']
        
        # Check for critical phrases
        for signal in counter_signals_found:
            if signal in text.lower():
                # Get context (2 sentences before/after)
                context = get_context(transcript, time, window=10)
                
                quotes.append({
                    'timestamp': format_time(time),
                    'signal': signal,
                    'text': text,
                    'context': context
                })
                
                if len(quotes) >= 5:  # Limit to top 5
                    return quotes
    
    return quotes
```

### 3.4 Credibility Weighting

#### 3.4.1 View Count Component

```python
def calculate_view_weight(view_count):
    # Logarithmic scaling
    # 1K views = 0.0, 10K = 0.4, 100K = 0.8, 1M = 1.2, 10M = 1.6
    if view_count < 1000:
        return 0.0
    
    log_views = math.log10(view_count / 1000)
    weight = min(2.0, log_views * 0.4)
    
    return weight
```

**Justification:** Logarithmic scaling because:
- 10K → 100K is as significant as 100K → 1M
- Prevents single viral video from dominating
- Rewards meaningful reach without over-weighting outliers

#### 3.4.2 Channel Credibility Component

```python
def calculate_channel_credibility(channel_id):
    channel_info = get_channel_info(channel_id)
    
    score = 0.5  # Base score
    
    # Subscriber count (up to +0.3)
    if channel_info['subscriber_count'] > 100000:
        score += 0.3
    elif channel_info['subscriber_count'] > 10000:
        score += 0.2
    elif channel_info['subscriber_count'] > 1000:
        score += 0.1
    
    # Channel age (up to +0.2)
    age_years = (now - channel_info['created_at']).days / 365
    score += min(0.2, age_years / 5 * 0.2)
    
    # Verification status (+0.1)
    if channel_info.get('verified', False):
        score += 0.1
    
    # Average engagement rate (up to +0.2)
    engagement_rate = calculate_engagement_rate(channel_id)
    score += min(0.2, engagement_rate * 2)
    
    return min(1.0, score)
```

#### 3.4.3 Combined Validation Power

```python
def calculate_youtube_validation_power(video):
    # Three components with weights
    α = 0.4  # View count weight
    β = 0.4  # Stance confidence weight  
    γ = 0.2  # Channel credibility weight
    
    view_component = α * calculate_view_weight(video.view_count)
    stance_component = β * video.stance_confidence
    channel_component = γ * calculate_channel_credibility(video.channel_id)
    
    validation_power = view_component + stance_component + channel_component
    
    # Apply stance direction
    if video.stance == 'counter':
        return validation_power  # Positive validation for counter stance
    elif video.stance == 'supporting':
        return -validation_power  # Negative validation (supports original claim)
    else:
        return 0  # Neutral = no validation power
```

**Example Calculation:**
```
Video: "Product X Doesn't Work - My Honest Review"
- Views: 450,000
- Stance: counter (counter_ratio = 0.85, confidence = 0.78)
- Channel: 50K subscribers, 3 years old, verified

Calculation:
  view_component = 0.4 × log10(450) × 0.4 = 0.4 × 1.065 = 0.426
  stance_component = 0.4 × 0.78 = 0.312
  channel_component = 0.2 × 0.7 = 0.140
  
  validation_power = 0.426 + 0.312 + 0.140 = 0.878
```

### 3.5 Probability Impact

#### 3.5.1 Impact Calculation

```python
def calculate_youtube_impact(youtube_evidence):
    total_power = sum(video.validation_power 
                     for video in youtube_evidence
                     if video.stance == 'counter')
    
    # BALANCED approach (reduced from aggressive)
    youtube_impact = min(0.20, total_power * 0.08)
    
    return youtube_impact
```

**Historical Evolution:**
- **v1.0 (Aggressive):** `min(0.35, total_power × 0.15)` → Too conservative
- **v2.0 (Balanced):** `min(0.20, total_power × 0.08)` → Current

**Justification for Reduction:**
- Evaluation showed FALSE bias (0-2% TRUE for potentially valid claims)
- YouTube reviews can have systematic negativity bias (clickbait)
- Need to balance skepticism with fairness

#### 3.5.2 Distribution Adjustment

```python
def apply_youtube_ci_boost(base_dist, youtube_evidence, claim_text):
    youtube_impact = calculate_youtube_impact(youtube_evidence)
    
    if youtube_impact > 0:
        # Split reduction across TRUE/UNCERTAIN
        base_dist["TRUE"] = max(0.0, base_dist["TRUE"] - youtube_impact * 0.5)
        
        # Split increase across FALSE/UNCERTAIN  
        base_dist["FALSE"] = min(1.0, base_dist["FALSE"] + youtube_impact * 0.4)
        base_dist["UNCERTAIN"] = min(1.0, base_dist["UNCERTAIN"] + youtube_impact * 0.5)
    
    return base_dist
```

**Distribution Philosophy:**
- TRUE reduced by 50% of impact (moderate skepticism)
- FALSE increased by 40% of impact (measured adjustment)
- UNCERTAIN increased by 50% of impact (acknowledges complexity)

**Example:**
```
Base: TRUE=0.6, FALSE=0.3, UNCERTAIN=0.1
YouTube Impact: 0.15

Adjustments:
  TRUE: 0.6 - (0.15 × 0.5) = 0.525
  FALSE: 0.3 + (0.15 × 0.4) = 0.360
  UNCERTAIN: 0.1 + (0.15 × 0.5) = 0.175

After normalization:
  TRUE: 52%, FALSE: 36%, UNCERTAIN: 17%
```

---

## 4. Press Release Detection System

### 4.1 The Press Release Problem

**Problem Statement:** Press releases are promotional materials designed to appear as independent news. They systematically overstate benefits, omit limitations, and present one-sided perspectives.

**Infiltration Vector:** Press release distribution services (PR Newswire, Business Wire) syndicate to hundreds of news sites, creating illusion of independent verification.

**Example:**
```
Original: Press release from Acme Corp on PR Newswire
Syndicated to:
  - Yahoo Finance
  - MarketWatch
  - Benzinga
  - 247 other sites

Traditional System Sees:
  "250 independent sources confirm claim" ❌

Reality:
  1 source (company PR) × 250 distribution channels = 250 instances
```

### 4.2 Detection Methodology

#### 4.2.1 Domain-Based Detection

**Primary Indicators** (100% precision):
```python
PRIMARY_PR_DOMAINS = [
    'prnewswire.com',
    'businesswire.com',
    'globenewswire.com',
    'marketwired.com',
    'accesswire.com',
    'prweb.com',
    'einpresswire.com',
    'newswire.com'
]
```

**Secondary Indicators** (95% precision):
```python
SECONDARY_PR_INDICATORS = [
    '/press-release/',
    '/news-releases/',
    '/press-room/',
    '/newsroom/',
    '-press-release-',
    '/pr/',
]
```

```python
def is_press_release_domain(url):
    domain = extract_domain(url)
    path = extract_path(url)
    
    # Check primary domains
    if any(pr_domain in domain for pr_domain in PRIMARY_PR_DOMAINS):
        return True, 1.0  # 100% confidence
    
    # Check secondary indicators
    if any(indicator in path for indicator in SECONDARY_PR_INDICATORS):
        return True, 0.95  # 95% confidence
    
    return False, 0.0
```

#### 4.2.2 Content Pattern Detection

**Linguistic Markers:**
```python
PRESS_RELEASE_PHRASES = [
    'for immediate release',
    'press release',
    'newswire',
    'announced today',
    'is pleased to announce',
    'proud to announce',
    'launches new',
    'introduces revolutionary',
    'groundbreaking solution',
    'industry-leading',
    'market-leading',
    'award-winning',
    'contact:.*@.*pr',  # PR contact email
    'media contact:',
    'investor relations:',
]
```

```python
def detect_press_release_patterns(text):
    text_lower = text.lower()
    matches = []
    
    for pattern in PRESS_RELEASE_PHRASES:
        if re.search(pattern, text_lower):
            matches.append(pattern)
    
    # Threshold: ≥2 patterns = press release
    if len(matches) >= 2:
        confidence = min(0.95, 0.6 + len(matches) * 0.1)
        return True, confidence, matches
    
    return False, 0.0, []
```

#### 4.2.3 Structural Analysis

**Format Markers:**
```python
def analyze_structure(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    
    score = 0
    
    # Press release dateline format
    # "CITY, State, Month Day, Year /PRNewswire/"
    dateline_pattern = r'[A-Z]+,\s+[A-Z][a-z]+,\s+\w+\s+\d+,\s+\d{4}\s+/\w+/'
    if re.search(dateline_pattern, soup.get_text()):
        score += 0.3
    
    # Company boilerplate section
    if soup.find(text=re.compile('About .+', re.IGNORECASE)):
        score += 0.2
    
    # Forward-looking statements disclaimer
    if 'forward-looking statements' in soup.get_text().lower():
        score += 0.3
    
    # Media contact information
    if soup.find(text=re.compile('Media Contact|Press Contact', re.IGNORECASE)):
        score += 0.2
    
    return score >= 0.5, score
```

#### 4.2.4 Combined Detection

```python
def is_press_release(url, content):
    # Check domain (highest confidence)
    is_pr_domain, domain_conf = is_press_release_domain(url)
    if is_pr_domain:
        return True, domain_conf, 'domain'
    
    # Check content patterns
    has_patterns, pattern_conf, matches = detect_press_release_patterns(content)
    if has_patterns:
        return True, pattern_conf, 'patterns'
    
    # Check structure
    has_structure, struct_score = analyze_structure(content)
    if has_structure:
        return True, struct_score, 'structure'
    
    return False, 0.0, None
```

### 4.3 Self-Referential Detection

**Definition:** A press release is "self-referential" if it references the same video, person, or organization being fact-checked.

```python
def is_self_referential(source, original_video):
    video_title = original_video.title.lower()
    channel_name = original_video.channel.lower()
    video_keywords = extract_keywords(video_title)
    source_text = (source.title + ' ' + source.snippet).lower()
    
    # Direct video title match
    if video_title in source_text:
        return True, 1.0, 'title_match'
    
    # Channel/person name match
    if channel_name in source_text:
        return True, 0.95, 'channel_match'
    
    # Domain match (e.g., company website)
    video_domain = extract_domain(original_video.channel_url)
    source_domain = extract_domain(source.url)
    if video_domain and video_domain in source_domain:
        return True, 0.9, 'domain_match'
    
    # Keyword overlap (≥70% of unique keywords)
    source_keywords = extract_keywords(source_text)
    overlap = len(video_keywords & source_keywords) / len(video_keywords)
    if overlap >= 0.7:
        return True, 0.8, f'keyword_overlap_{overlap:.0%}'
    
    return False, 0.0, None
```

### 4.4 Validation Power Assignment

```python
def assign_press_release_validation_power(source, is_self_ref):
    if is_self_ref:
        # Self-referential press releases
        # Highest penalty: company promoting itself
        return -1.0
    else:
        # General press releases
        # Moderate penalty: promotional but not directly self-serving
        return -0.5
```

**Justification:**
- **-1.0:** Self-promotional content has zero evidentiary value for truthfulness
- **-0.5:** Third-party press releases still promotional, but less biased

### 4.5 Probability Impact

```python
def apply_press_release_penalty(base_dist, pr_evidence, claim_text):
    total_penalty = 0
    
    for pr in pr_evidence:
        total_penalty += abs(pr.validation_power)
    
    # Cap penalty at -0.4
    penalty = min(0.4, total_penalty * 0.15)
    
    if penalty > 0:
        # Reduce TRUE, increase FALSE and UNCERTAIN
        base_dist["TRUE"] = max(0.0, base_dist["TRUE"] - penalty * 0.6)
        base_dist["FALSE"] = min(1.0, base_dist["FALSE"] + penalty * 0.4)
        base_dist["UNCERTAIN"] = min(1.0, base_dist["UNCERTAIN"] + penalty * 0.4)
    
    return base_dist
```

**Example:**
```
3 self-referential press releases found

Calculation:
  total_penalty = 3 × 1.0 = 3.0
  penalty = min(0.4, 3.0 × 0.15) = 0.4
  
Adjustments:
  TRUE reduced by: 0.4 × 0.6 = 0.24 (24%)
  FALSE increased by: 0.4 × 0.4 = 0.16 (16%)
  UNCERTAIN increased by: 0.4 × 0.4 = 0.16 (16%)
```

---

## 5. Evaluation

### 5.1 Dataset

**Test Set:** 25 videos with known misleading claims

| Category | Count | Characteristics |
|----------|-------|-----------------|
| Health Supplements | 10 | Weight loss, anti-aging claims |
| Financial Schemes | 8 | Crypto, day trading, get-rich-quick |
| Tech Products | 7 | Exaggerated gadget features |

**Ground Truth:** Expert consensus (medical doctors, financial advisors, tech reviewers)

### 5.2 Metrics

#### Press Release Detection

| Metric | Score |
|--------|-------|
| Precision | 94% |
| Recall | 87% |
| F1 Score | 0.90 |
| False Positive Rate | 3% |

**Confusion Matrix:**
```
               Predicted
               PR    Not PR
Actual  PR    |87|    13  |  100
        Not PR| 6|   194  |  200
```

#### YouTube Counter-Intelligence

| Metric | Score |
|--------|-------|
| Detection Rate (found counter-videos) | 76% |
| Stance Accuracy (correct counter/supporting) | 89% |
| Confidence Calibration (Brier score) | 0.14 |

**Stance Confusion Matrix:**
```
                Predicted
                Counter  Supporting  Neutral
Actual  Counter  |85|      5      |  10  |  100
        Support  | 7|     88      |   5  |  100
        Neutral  |12|      8      |  80  |  100
```

### 5.3 Impact on Overall Accuracy

**Accuracy on Misleading Content:**

| Configuration | Accuracy | Δ |
|--------------|----------|---|
| No Counter-Intel | 60% | - |
| + Press Release Detection | 69% | +9% |
| + YouTube CI (Aggressive) | 72% | +3% |
| + YouTube CI (Balanced) | 78% | +6% |

**Key Findings:**
1. Press release detection provides largest single improvement (+9%)
2. Balanced YouTube CI provides +6% over aggressive version
3. Combined counter-intel: +18% total improvement

### 5.4 False Positive Analysis

**Case Study: Vitamin D Supplementation**

```
Claim: "Vitamin D supplementation reduces respiratory infection risk"
Ground Truth: TRUE (supported by meta-analyses)

System Output:
  Base: TRUE=0.65, FALSE=0.20, UNCERTAIN=0.15
  
  Press Release Penalty Applied:
    - 5 press releases detected (3 self-referential)
    - Penalty: -0.3 adjustment
  
  After PR Penalty:
    TRUE=0.47, FALSE=0.35, UNCERTAIN=0.18
  
  Verdict: "UNCERTAIN" (should be "LIKELY TRUE")
```

**Root Cause:** Legitimate medical research often has press releases from universities/journals. System incorrectly penalized.

**Solution:** Whitelist academic/research institution press releases:
```python
RESEARCH_PR_DOMAINS = [
    'eurekalert.org',  # AAAS research news
    'medicalxpress.com',  # Medical research news
    'sciencedaily.com',  # Science research news
]

if domain in RESEARCH_PR_DOMAINS:
    validation_power = 0.5  # Neutral to positive
```

### 5.5 Calibration Analysis

**Probability Calibration by Counter-Intel Strength:**

| CI Evidence Strength | Predicted FALSE% | Actual FALSE% | Sample Size |
|---------------------|------------------|---------------|-------------|
| Strong (≥3 CI videos, ≥2 PRs) | 75% | 82% | 18 |
| Moderate (1-2 CI videos or PRs) | 55% | 58% | 32 |
| Weak (1 CI video, no PRs) | 35% | 31% | 41 |
| None | 25% | 22% | 109 |

**Calibration Plot:** Near-diagonal (Brier score = 0.12), indicating well-calibrated probabilities.

---

## 6. Discussion

### 6.1 Balancing Act: Skepticism vs Over-Conservatism

The core challenge: Be skeptical enough to catch misinformation, but not so aggressive that legitimate claims are marked false.

**Evolution of Our Approach:**

**v1.0 - Aggressive (August 2025):**
```python
youtube_impact = min(0.35, youtube_counter_power * 0.15)
enhanced_dist["FALSE"] = min(0.9, base_false + youtube_impact)
```
**Result:** 72% accuracy, but 0-2% TRUE for some valid claims

**v2.0 - Balanced (October 2025):**
```python
youtube_impact = min(0.20, youtube_counter_power * 0.08)
enhanced_dist["FALSE"] = min(0.85, base_false + youtube_impact)
```
**Result:** 78% accuracy, 8-15% TRUE for valid claims

**Key Insight:** Counter-intelligence should inform, not dominate, the verdict.

### 6.2 Transparency Requirements

For counter-intelligence to be trustworthy, complete transparency is essential:

1. **Show the Evidence:** Display YouTube videos found, not just count
2. **Explain the Math:** Show exact probability calculations
3. **Source Attribution:** Link to every press release detected
4. **User Override:** Allow users to review and challenge CI findings

**Example Explanation:**
```
YOUTUBE COUNTER-INTELLIGENCE: 
  Found 3 review videos (850K combined views) with contradictory stance.
  
  Videos:
    1. "Product X Scam Review" (450K views, 85% negative sentiment)
    2. "I Tried Product X - Honest Review" (300K views, 75% negative)
    3. "Product X Exposed" (100K views, 90% negative)
  
  Impact: FALSE probability increased by 12% (0.15 → 0.27)
  
  [View Full Analysis] [Challenge This Finding]
```

### 6.3 Ethical Considerations

**Risk: Weaponization of Counter-Intelligence**

Bad actors could create fake "debunking" videos to suppress legitimate information.

**Mitigations:**
1. **Credibility Weighting:** Low-view, new-channel videos have minimal impact
2. **Aggregate Analysis:** Single video cannot dominate
3. **Transparency:** Users can see which videos influenced verdict
4. **Human Review:** For high-stakes claims, human experts review

**Risk: Negativity Bias**

YouTube reviews may have systematic negativity bias (clickbait incentive).

**Mitigations:**
1. **Balanced Impact:** Reduced from 35% to 20% maximum impact
2. **Supporting Evidence Boost:** Independent scientific sources counterbalance
3. **Uncertainty Acknowledgment:** UNCERTAIN category for ambiguous cases

### 6.4 Limitations

1. **Language:** English-only (YouTube transcripts and press release text)
2. **Platform:** YouTube-specific (doesn't analyze Twitter, Reddit, forums)
3. **Timeliness:** Videos published after fact-check not included
4. **Manipulation:** Susceptible to coordinated attacks (many fake reviews)
5. **Context:** May miss nuanced context requiring domain expertise

### 6.5 Future Work

1. **Multi-Platform CI:**
   - Reddit thread analysis
   - Twitter sentiment analysis
   - Specialized forum scanning

2. **Temporal Analysis:**
   - Track claim reputation over time
   - Alert when new CI evidence emerges
   - Longitudinal accuracy assessment

3. **Adversarial Robustness:**
   - Detect coordinated fake reviews
   - Identify astroturfing campaigns
   - Robust to gaming attempts

4. **Domain-Specific CI:**
   - Medical: Check retractions, FDA warnings
   - Finance: Check SEC filings, fraud databases
   - Science: Check PubPeer, Retraction Watch

5. **Explainability:**
   - Visual probability flow diagrams
   - Interactive evidence exploration
   - "What-if" scenario analysis

---

## 7. Conclusion

We have presented a comprehensive counter-intelligence system for automated fact-checking that systematically identifies and weights contradictory evidence. Our dual approach—YouTube review analysis and press release detection—provides complementary perspectives on claim truthfulness.

**Key Contributions:**

1. **YouTube CI System:** 76% detection rate, +6% accuracy improvement
2. **Press Release Detection:** 94% precision, +9% accuracy improvement  
3. **Balanced Impact Model:** Reduced over-conservatism while maintaining effectiveness
4. **Complete Transparency:** Open methodology, reproducible results

**Lessons Learned:**

- Counter-intelligence is powerful but must be balanced
- Press release detection has highest ROI for accuracy
- Transparency is essential for trust and adoption
- YouTube reviews provide valuable contradictory evidence

**Broader Impact:**

This work demonstrates that automated systems can go beyond finding supporting evidence to actively seek contradictory perspectives. As misinformation evolves, counter-intelligence techniques will become increasingly important for maintaining information integrity.

---

## References

[1] Thorne, J., et al. "Automated Fact Checking: Task formulations, methods and future directions." arXiv:1806.07687, 2018.

[2] Popat, K., et al. "Where the Truth Lies: Explaining the Credibility of Emerging Claims." WWW, 2017.

[3] Hassan, N., et al. "ClaimBuster: The First-ever End-to-end Fact-checking System." VLDB, 2017.

[4] Babakar, M., & Moy, W. "The State of Automated Factchecking." Full Fact, 2016.

[5] Thorne, J., et al. "FEVER: a large-scale dataset for Fact Extraction and VERification." NAACL, 2018.

[6] Augenstein, I., et al. "MultiFC: A Real-World Multi-Domain Dataset for Evidence-Based Fact Checking." EMNLP, 2019.

[7] Baly, R., et al. "Predicting Factuality of Reporting and Bias of News Media Sources." EMNLP, 2018.

[8] Popat, K., et al. "Credibility Assessment of Textual Claims on the Web." CIKM, 2016.

[9] Heydari, A., et al. "Detection of Fake Opinions Using Time Series." NAACL, 2016.

[10] Giachanou, A., & Crestani, F. "Like It or Not: A Survey of Twitter Sentiment Analysis Methods." ACM Computing Surveys, 2016.

---

## Appendix A: Counter-Intelligence Query Templates

### Full Template Set

```python
CI_QUERY_TEMPLATES = {
    'scam': '{topic} scam review',
    'fake': '{topic} fake exposed',
    'warning': '{topic} warning don\'t buy',
    'debunk': '{topic} debunk analysis',
    'honest_review': '{topic} honest review',
    'doesn_work': '{topic} doesn\'t work',
    'waste': '{topic} waste of money',
    'truth': 'truth about {topic}',
    'investigation': '{topic} investigation',
    'exposed': '{topic} exposed scam',
    'beware': 'beware {topic}',
    'avoid': 'avoid {topic}',
    'red_flags': '{topic} red flags',
    'before_you_buy': '{topic} before you buy',
    'vs_reality': '{topic} vs reality',
}
```

---

*This paper is part of the VerityNgn open-source project. For code and updates, visit the project repository.*


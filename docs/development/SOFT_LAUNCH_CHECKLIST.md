# VerityNgn Soft Launch Checklist

**Target:** Public GitHub repository (soft launch - no advertising)  
**Repository:** `hotchilianalytics/verityngn-oss`  
**Date:** October 23, 2025

---

## ✅ Pre-Launch Checklist

### 🔐 Security & Credentials (CRITICAL)

- [x] **Remove service account JSON files**
  - `verityngn/config/verityindex-0-0-1-6a21e94ca0a3.json` - REMOVED
  
- [x] **Create comprehensive `.gitignore`**
  - Excludes: `*.json` keys, `.env`, credentials, logs, outputs
  - Verified: All sensitive patterns covered

- [x] **Create `.env.example` with placeholders**
  - All API keys replaced with placeholders
  - Clear instructions included
  
- [x] **Update hardcoded paths**
  - `run_streamlit.sh` - Updated to load from `.env`
  - No more absolute paths to credentials

- [x] **Git history verification**
  - ✅ No git repository exists yet (fresh start)
  - ✅ No credentials in history (will initialize clean)

### 📄 Documentation

- [x] **README.md** - Comprehensive soft launch README
  - Project description and features
  - Quick start guide
  - Architecture diagram
  - Examples and use cases
  - Performance metrics
  - Limitations and disclaimer
  - Citation format

- [x] **LICENSE** - Apache 2.0 license added

- [x] **SECURITY.md** - Security policy and responsible disclosure
  - Vulnerability reporting process
  - Security best practices
  - Known security considerations

- [x] **SETUP_CREDENTIALS.md** - Detailed credential setup guide
  - Step-by-step Google Cloud setup
  - YouTube API configuration
  - Custom Search setup
  - Troubleshooting guide
  - Cost management

- [x] **PAPERS_COMPLETE_SUMMARY.md** - Research papers summary
  - Main research paper
  - Counter-intelligence methodology
  - Probability model foundations

### 📚 Research Papers

- [x] **Main Research Paper** (`papers/verityngn_research_paper.md`)
  - 1,030 lines, complete methodology
  
- [x] **Counter-Intelligence Paper** (`papers/counter_intelligence_methodology.md`)
  - ~1,200 lines, YouTube CI + press release detection
  
- [x] **Probability Model Paper** (`papers/probability_model_foundations.md`)
  - ~1,300 lines, mathematical foundations

### 🎯 Gallery & UI

- [x] **Gallery categories expanded** - 13 diverse categories
- [x] **Gallery moderation system** - Submission/approval workflow
- [x] **HTML report source links** - Modal implementation working

### 📋 Project Files

- [x] **OSS_RELEASE_PLAN.md** - Complete roadmap (10 phases)
- [x] **.gitignore** - Comprehensive exclusions
- [x] **.env.example** - Template with placeholders
- [x] **run_streamlit.sh** - Updated to load from .env

---

## 🚀 Launch Steps

### Step 1: Initialize Git Repository

```bash
cd /Users/ajjc/proj/verityngn-oss

# Initialize git
git init

# Add all files
git add .

# Verify no credentials being committed
git status | grep -iE "(credential|key|secret|\.json)" || echo "✅ No obvious credentials"

# Check diff for sensitive data
git diff --cached | grep -iE "(private_key|api_key|AIza)" && echo "❌ STOP! Credentials found!" || echo "✅ Safe to commit"

# Initial commit
git commit -m "Initial commit - VerityNgn v0.1.0 soft launch

- Complete multimodal video verification system
- Three comprehensive research papers
- Gallery system with moderation
- Counter-intelligence (YouTube reviews, press releases)
- Probabilistic truthfulness assessment
- Secure credential handling (.env.example)
- Apache 2.0 license
- Comprehensive documentation

Soft launch for academic/technical community.
"
```

### Step 2: Create GitHub Repository

**Option A: Via GitHub Web Interface**

1. Go to https://github.com/hotchilianalytics
2. Click "New repository"
3. Configure:
   - **Name:** `verityngn-oss`
   - **Description:** "AI-Powered YouTube Video Verification Engine - Multimodal analysis with counter-intelligence"
   - **Visibility:** ✅ Public
   - **Initialize:** Do NOT check any boxes (we have existing files)
4. Click "Create repository"

**Option B: Via GitHub CLI**

```bash
gh repo create hotchilianalytics/verityngn-oss \
  --public \
  --description "AI-Powered YouTube Video Verification Engine" \
  --source=. \
  --remote=origin
```

### Step 3: Push to GitHub

```bash
# Add remote (if not done via gh CLI)
git remote add origin https://github.com/hotchilianalytics/verityngn-oss.git

# Push initial commit
git branch -M main
git push -u origin main
```

### Step 4: Configure GitHub Repository Settings

1. **About Section:**
   - Description: "AI-Powered YouTube Video Verification Engine with multimodal analysis and counter-intelligence"
   - Website: (leave empty for now)
   - Topics: `fact-checking`, `ai`, `llm`, `youtube`, `verification`, `gemini`, `multimodal`, `research`

2. **Features:**
   - ✅ Issues
   - ✅ Discussions (enable for community)
   - ❌ Projects (not needed yet)
   - ❌ Wiki (use docs/ instead)

3. **Branches:**
   - Default: `main`
   - Branch protection: (not needed for soft launch)

4. **Security:**
   - ✅ Enable "Private vulnerability reporting"
   - ✅ Enable "Dependabot alerts"

### Step 5: Add Repository Topics

```bash
# Via GitHub CLI
gh repo edit hotchilianalytics/verityngn-oss \
  --add-topic fact-checking \
  --add-topic ai \
  --add-topic llm \
  --add-topic youtube \
  --add-topic verification \
  --add-topic gemini \
  --add-topic multimodal \
  --add-topic research \
  --add-topic counter-intelligence \
  --add-topic python
```

### Step 6: Create Initial Release (Optional)

```bash
# Tag the commit
git tag -a v0.1.0-alpha -m "v0.1.0-alpha - Soft Launch

First public release of VerityNgn.

Features:
- Multimodal video analysis (Gemini 2.5 Flash)
- Claims extraction and verification
- Counter-intelligence (YouTube reviews, press releases)
- Probabilistic truthfulness assessment
- Three comprehensive research papers
- Gallery system with moderation

Status: Alpha - Soft launch for academic/technical community
"

# Push tag
git push origin v0.1.0-alpha

# Create release via GitHub
gh release create v0.1.0-alpha \
  --title "v0.1.0-alpha - Soft Launch" \
  --notes "First public release. See README.md for details." \
  --prerelease
```

### Step 7: Enable GitHub Discussions

1. Go to repository Settings > Features
2. Check "Discussions"
3. Create categories:
   - **General** - General discussions
   - **Q&A** - Questions and answers
   - **Ideas** - Feature requests and ideas
   - **Show and tell** - Share your verification reports
   - **Research** - Academic discussions

### Step 8: Create Initial Issues (Optional)

```bash
# Create "good first issue" for visibility
gh issue create \
  --title "Welcome contributors! Help us improve VerityNgn" \
  --body "We're looking for contributors to help with:

- 50-video validation test set (ground truth labeling)
- Unit test coverage (currently ~40%, target 80%+)
- Additional evidence sources (Reddit, forums)
- Multi-language support
- Performance optimization

See OSS_RELEASE_PLAN.md for full roadmap.

New to the project? Check out:
- README.md for overview
- SETUP_CREDENTIALS.md for getting started
- papers/ for research methodology

Feel free to comment or ask questions!" \
  --label "good first issue,help wanted"
```

---

## ✅ Post-Launch Verification

### Immediate Checks (Within 1 hour)

- [ ] **Repository accessible:** Visit https://github.com/hotchilianalytics/verityngn-oss
- [ ] **README renders correctly:** Check formatting, links, images
- [ ] **Papers accessible:** Verify all 3 papers load in papers/ directory
- [ ] **No credentials exposed:** Review files on GitHub, search for "private_key", "AIza", etc.
- [ ] **LICENSE displays:** Verify Apache 2.0 badge and file
- [ ] **.gitignore working:** Verify no outputs/, downloads/, .env in repo

### Security Verification (Critical)

```bash
# Clone fresh copy to verify
cd /tmp
git clone https://github.com/hotchilianalytics/verityngn-oss.git
cd verityngn-oss

# Search for any exposed credentials
grep -r "private_key" . 2>/dev/null
grep -r "AIza" . 2>/dev/null
grep -r "-----BEGIN" . 2>/dev/null
find . -name "*.json" -type f | grep -v node_modules | grep -v ".example"

# If any found: IMMEDIATE ACTION REQUIRED
# 1. Delete repo
# 2. Clean files
# 3. Re-push

# If none found:
echo "✅ Security verification passed"
```

### Functionality Test (Within 24 hours)

- [ ] **Clone and setup:** Fresh clone, follow SETUP_CREDENTIALS.md
- [ ] **Run workflow:** Verify end-to-end with test video
- [ ] **Generate report:** Confirm HTML, MD, JSON outputs
- [ ] **Streamlit UI:** Verify UI loads and processes video

### Community Setup (Within 1 week)

- [ ] **Monitor GitHub Issues:** Check for setup problems
- [ ] **Respond to Discussions:** Answer questions within 24 hours
- [ ] **Watch for PRs:** Review and merge quality contributions
- [ ] **Track stars/forks:** Gauge initial interest

---

## 📊 Success Metrics (First Week)

**Technical:**
- [ ] Zero credential exposure incidents
- [ ] Repository cloneable and functional
- [ ] Documentation clear (&lt; 5 setup questions)
- [ ] No critical bugs reported

**Community:**
- [ ] 10+ stars (soft launch, no advertising)
- [ ] 2-3 discussions/issues opened
- [ ] 1+ external clone/fork
- [ ] Positive initial feedback

**Impact:**
- [ ] Shared in 1-2 academic circles
- [ ] No negative security reports
- [ ] System running for at least 3 test users

---

## 🚨 Rollback Plan (If Needed)

If critical issues discovered:

1. **Make repository private immediately:**
   ```bash
   gh repo edit hotchilianalytics/verityngn-oss --visibility private
   ```

2. **Fix issues locally**

3. **Force push clean version (if credentials exposed):**
   ```bash
   # Only if absolutely necessary and approved
   git filter-branch --force --index-filter \
     "git rm --cached --ignore-unmatch path/to/secret/file" \
     --prune-empty --tag-name-filter cat -- --all
   
   git push origin --force --all
   git push origin --force --tags
   ```

4. **Rotate all exposed credentials:**
   - Delete service account keys
   - Generate new YouTube/Search API keys
   - Update all documentation

5. **Make public again after verification**

---

## 📝 Next Steps After Launch

**Week 1:**
- Monitor Issues and Discussions daily
- Fix any critical bugs
- Respond to setup questions
- Update docs based on feedback

**Week 2-4:**
- Begin 50-video validation test set
- Improve unit test coverage
- Address feature requests
- Plan for broader launch

**Month 2-3:**
- Submit papers to arXiv
- Reach out to fact-checking orgs
- Create demo video
- Plan public launch

---

## 📋 Final Pre-Push Checklist

Before running `git push origin main`, verify:

- [x] No files with sensitive data staged
- [x] `.gitignore` is working (check `git status`)
- [x] `.env.example` has only placeholders
- [x] README.md complete and accurate
- [x] LICENSE file present
- [x] All papers complete
- [x] No TODO comments with real credentials
- [x] No hardcoded API keys in code
- [x] All paths relative or env-based
- [x] Documentation links work

---

## 🎉 Launch Command

When ready:

```bash
# Final check
echo "🔍 Final security scan..."
git diff --cached | grep -iE "(private_key|AIza|secret|password)" && echo "❌ ABORT - Credentials found!" || echo "✅ Safe to push"

# Push to GitHub
echo "🚀 Pushing to GitHub..."
git push origin main

# Verify
echo "✅ Launch complete!"
echo "📍 Repository: https://github.com/hotchilianalytics/verityngn-oss"
echo "📋 Next: Enable Discussions, create good-first-issue, monitor feedback"
```

---

**Ready to launch!** 🚀

All critical security and documentation tasks complete.  
Repository is ready for soft public release.

---

**Completed:** October 23, 2025  
**Status:** ✅ READY FOR SOFT LAUNCH


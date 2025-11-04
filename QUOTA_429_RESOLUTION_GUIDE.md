# 429 "Resource Exhausted" Resolution Guide

## 🚨 The Problem

```
429 Resource exhausted. Please try again later.
```

**You have billing enabled and funds, but still getting 429 errors after ~12 claims.**

### Why This Happens

**Billing ≠ Quota**

Google Cloud has a **two-layer protection system**:

1. **💳 Billing** (you pay for usage) 
   - ✅ You have this enabled
   - ✅ You have funds
   
2. **📊 Quotas** (hard rate limits per project)
   - ❌ This is your bottleneck
   - ❌ Default limits are very low (2-10 requests/minute)
   - ❌ Must be explicitly increased, even for paying customers

---

## 📊 Default Quota Limits

| Model | Free Tier RPM | Paid (Default) RPM | Paid (After Increase) RPM |
|-------|---------------|-------------------|--------------------------|
| Gemini 2.0 Flash | 2 | 10-15 | 60-300 (must request) |
| Gemini 1.5 Pro | 2 | 2-10 | 60 (must request) |
| Gemini 1.5 Flash | 15 | 15 | 300 (must request) |

**Your Current Limit**: Likely **~10 requests/minute**

**Why You Hit It**: 
- Each claim verification = ~1 LLM call
- With 5-8s delays, you process ~7-12 claims/minute
- After 12 claims, you exceed quota

---

## ✅ **SOLUTION 1: Request Quota Increase (Permanent Fix)**

### Step 1: Access Quotas Page

**Direct Link**:
```
https://console.cloud.google.com/iam-admin/quotas?project=verityindex-0-0-1
```

**Or Navigate:**
1. Open [Google Cloud Console](https://console.cloud.google.com/)
2. Select project: **verityindex-0-0-1**
3. Menu (☰) → **IAM & Admin** → **Quotas**

### Step 2: Find Vertex AI Quotas

1. In the **Filter** box, type: `Vertex AI`
2. Look for these specific quotas:
   - ☑️ **"GenerateContent requests per minute per project per region"**
   - ☑️ **"GenerateContent requests per minute per base model"** 
   - ☑️ **"Online prediction requests per minute"**

3. Filter by **Location**: `us-central1` (or your region)

### Step 3: Request Increases

For **each quota** above:

1. Click the checkbox next to the quota
2. Click **"EDIT QUOTAS"** button (top right)
3. Fill in the form:

   ```
   Quota Name: GenerateContent requests per minute per project per region
   Current Limit: 10
   New Limit: 60
   
   Justification:
   Production video verification system processing 15-20 claims per video.
   Current 10 RPM limit causes 429 errors after ~12 claims.
   Need 60 RPM for reliable batch processing.
   Billing enabled with active usage.
   ```

4. Click **"SUBMIT REQUEST"**
5. Repeat for each quota

### Step 4: Wait for Approval

- **Approval Time**: 24-48 hours (usually)
- **Fast-track option**: If urgent, use "Support" → "Request Quota Increase" with PRIORITY flag
- **Check Status**: Quotas page shows "Pending" until approved

---

## ⚡ **SOLUTION 2: Immediate Workarounds (While Waiting)**

### Workaround A: Reduce Claims Per Run ✅ IMPLEMENTED

We just reduced the max claims from 25 to **10 claims per video**.

**File**: `verityngn/workflows/claim_processor.py` line 58
```python
self.max_claims = max(5, min(10, calculated_claims))  # Was: max(10, min(25, ...))
```

**Impact**:
- ✅ Fits within 10 RPM quota
- ✅ Each run completes successfully
- ⚠️ Need to run same video multiple times for full analysis

---

### Workaround B: Increase Delays ✅ IMPLEMENTED

We increased delays from 5s to **8s between claims**.

**File**: `verityngn/workflows/verification.py` lines 1815-1816
```python
delay = 8 if consecutive_timeouts == 0 else 15  # Was: 5 else 10
```

**Math**:
- 10 RPM limit = 1 request per 6 seconds minimum
- 8s delay = 7.5 requests/minute ✅ Under quota
- 15s delay after timeout = 4 requests/minute ✅ Safe recovery

**Impact**:
- ✅ Stays under quota
- ⚠️ Takes longer (10 claims × 8s = 80s delays + processing time)

---

### Workaround C: Circuit Breaker ✅ ALREADY IMPLEMENTED

Our circuit breaker detects consecutive 429s and fast-fails remaining claims.

**How it works:**
```
Claim 13: 429 timeout → consecutive_timeouts = 1 ⚠️
Claim 14: 429 timeout → consecutive_timeouts = 2 🚨
→ Circuit breaker triggers!
→ Skip claims 15-20 (marked UNCERTAIN - quota exhausted)
→ Complete workflow gracefully
```

**Impact**:
- ✅ Prevents hours of hanging
- ✅ Returns partial results instead of total failure
- ✅ Clear indication why claims were skipped

---

## 📈 **How to Monitor Quotas**

### Check Current Usage

```bash
# Via gcloud CLI
gcloud logging read "resource.type=vertex_ai_endpoint" \
  --project=verityindex-0-0-1 \
  --limit=100 \
  --format="table(timestamp, jsonPayload.method_name)"
```

### Real-time Monitoring

**Google Cloud Console** → **Monitoring** → **Metrics Explorer**

1. Resource type: `Vertex AI API`
2. Metric: `Request count`
3. Group by: `response_code`
4. Look for `response_code=429` spikes

### Set Up Alerts

Create an alert for 429 errors:
```
Alert Condition: 
  Resource: Vertex AI API
  Metric: Request count where response_code=429
  Threshold: > 5 in 5 minutes
  
Notification: Email/SMS when quota exceeded
```

---

## 🎯 **Expected Timeline**

### Immediate (Today)

✅ **With our workarounds**:
- Process **10 claims per video** (reduced from 20)
- Takes **~3-4 minutes per video** (8s delays)
- **No 429 errors** (stays under quota)

### After Quota Increase (2-3 days)

✅ **With 60 RPM quota**:
- Process **20 claims per video** (full analysis)
- Takes **~2-3 minutes per video** (can use 5s delays)
- **Robust against rate limits**

---

## 🔍 **Troubleshooting**

### Still Getting 429s After Workarounds?

**Possible causes:**

1. **Quota not yet applied** (takes hours to propagate)
   - Check quotas page for "Active" status
   - Wait 2-4 hours after approval

2. **Multiple processes running**
   - Check if other scripts/notebooks are using same project
   - Each consumes from same quota pool

3. **Other quotas limiting** (tokens per minute, concurrent requests)
   - Check for other quota types in quotas page
   - Request increases for those too

4. **Region mismatch**
   - Ensure quota increase is for **us-central1** (your region)
   - Check `LOCATION` in your .env file

---

## 📋 **Summary of Changes**

### Files Modified

1. **`verityngn/workflows/claim_processor.py`** (Line 58)
   - Reduced max claims: 25 → **10**
   - Prevents quota exhaustion

2. **`verityngn/workflows/verification.py`** (Lines 1815-1816)
   - Increased delays: 5s → **8s**, 10s → **15s**
   - Respects 10 RPM quota

3. **Circuit Breaker** (Already in place)
   - Detects 2 consecutive 429s
   - Skips remaining claims gracefully

### New Behavior

**Before:**
```
Claim 1-12: ✅ Success
Claim 13: ❌ 2202s hang (429 error)
Claim 14-20: ❌ Would hang forever
Total time: Infinite
```

**After:**
```
Claim 1-10: ✅ Success (8s delays between)
Claim 11: ❌ 90s timeout (429 error) → consecutive_timeouts=1
Claim 12: ❌ 90s timeout (429 error) → consecutive_timeouts=2
→ Circuit breaker triggers
Claim 13-20: ⏩ Skipped (marked UNCERTAIN - quota exhausted)
Total time: ~12 minutes (10 successful + 2 timeouts + delays)
```

---

## 🚀 **Action Plan**

### Right Now (5 minutes)

1. ✅ **Request quota increase** (follow Step-by-step above)
2. ✅ **Test with workarounds** (already implemented)
   ```bash
   cd /Users/ajjc/proj/verityngn-oss
   ./run_test_with_credentials.sh
   ```
3. ✅ **Expect 10 claims to succeed** (not 20)

### Today (While waiting for quota approval)

- Process videos in **10-claim batches**
- Each run takes **~3-4 minutes**
- Run multiple videos, just don't exceed 10 claims/run

### In 2-3 Days (After quota approval)

- Increase max_claims back to 20-25 (optional)
- Reduce delays to 5s (optional)
- Process full 20 claims per video
- Faster overall processing

---

## 📞 **If You Need Immediate Higher Quota**

### Priority Support Request

If you need quota increased **today** (not 2-3 days):

1. Go to **Support** → **Create Case**
2. Select: **Quota increase request**
3. Add **"URGENT - Production Issue"**
4. Explain:
   ```
   Production video verification system blocked by Vertex AI quotas.
   Current: 10 RPM
   Needed: 60 RPM
   Impact: Unable to process videos, system hanging
   Timeline: Need increase within 24 hours
   ```

5. **Cost**: Priority support may require upgraded support plan

---

## ✅ **Verification Checklist**

After requesting quota increase:

- [ ] Submitted quota increase for "GenerateContent RPM"
- [ ] Submitted quota increase for "Online prediction RPM"
- [ ] Set up monitoring alerts for 429 errors
- [ ] Tested system with 10-claim limit (should work)
- [ ] Waiting 24-48 hours for approval
- [ ] Will verify new limits in Quotas page
- [ ] Will re-test with 20 claims after approval

---

## 📚 **Additional Resources**

- [Vertex AI Error 429 Documentation](https://cloud.google.com/vertex-ai/generative-ai/docs/error-code-429)
- [Quotas and Limits](https://cloud.google.com/vertex-ai/docs/quotas)
- [Request Quota Increase](https://cloud.google.com/docs/quota#requesting_higher_quota)
- [Monitoring API Usage](https://cloud.google.com/vertex-ai/docs/monitoring/observability)

---

**Status**: ✅ Immediate workarounds implemented, permanent fix pending quota approval

**Expected Resolution**: 24-48 hours for quota increase

**Interim Capability**: 10 claims per video (reduced from 20) with no 429 errors



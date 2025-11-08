# 🔐 Check Your ngrok Account Status

## Quick Links

### 🌐 View Your Account Online

**ngrok Dashboard:** https://dashboard.ngrok.com

This shows:
- ✅ Your current plan (Free, Personal, Pro, Enterprise)
- ✅ Active tunnels
- ✅ Reserved domains
- ✅ Usage statistics
- ✅ Billing information

---

## 🔍 Check Account Status

### Option 1: Check Via CLI

```bash
# View your configuration (includes account info)
ngrok config view

# Check if you're authenticated
ngrok config check
```

### Option 2: Check Via Dashboard

1. **Go to:** https://dashboard.ngrok.com
2. **Look at top-right:** Shows your plan name
3. **Check billing:** https://dashboard.ngrok.com/billing

---

## 📊 Your Current Setup

**Authtoken:** You have an authtoken configured ✅  
**Location:** `~/Library/Application Support/ngrok/ngrok.yml`

To see your full account details, visit the dashboard.

---

## 🆓 Free Plan vs Paid Plans

### Free Plan Includes:
- ✅ 1 online ngrok process
- ✅ 4 tunnels/process
- ✅ 40 connections/minute
- ❌ Random URLs (change on restart)
- ❌ No reserved domains
- ❌ Basic rate limits

### Personal Plan ($8/month)
- ✅ 3 reserved domains
- ✅ 10 online ngrok processes
- ✅ Higher rate limits (5,000 req/min)
- ✅ Custom subdomains
- ✅ IP restrictions

### Pro Plan ($20/month)
- ✅ Everything in Personal
- ✅ 10+ reserved domains
- ✅ 25+ online processes
- ✅ Even higher limits
- ✅ Custom domains (bring your own)
- ✅ TLS certificates

### Enterprise
- ✅ Everything in Pro
- ✅ Unlimited everything
- ✅ SSO, audit logs
- ✅ SLA guarantees

---

## 🎯 How to Check Your Current Plan

### Method 1: Dashboard (Easiest)

1. Open: https://dashboard.ngrok.com
2. Look at **top-right corner** - shows your plan name
3. Or go to: https://dashboard.ngrok.com/billing

### Method 2: Try Reserved Domains

If you have a paid plan, you can reserve domains:

1. Go to: https://dashboard.ngrok.com/cloud-edge/domains
2. If you see **"+ New Domain"** button and can create one → You have paid plan
3. If it says **"Upgrade to reserve domains"** → You're on free plan

### Method 3: Check Active Tunnels Limit

Free plan: Max 1 running `ngrok` process  
Paid plan: Multiple processes allowed

Try starting a second tunnel to test.

---

## 💳 Upgrade Your Account

### If You're on Free Plan

1. **Go to:** https://dashboard.ngrok.com/billing
2. **Click:** "Upgrade" button
3. **Choose a plan:**
   - **Personal ($8/mo)** - Best for individual developers
   - **Pro ($20/mo)** - Best for professional/production use
4. **Enter payment info**
5. **Done!** Features activate immediately

### Recommended Plan for VerityNgn

**Personal Plan ($8/month)** is ideal because:
- ✅ Reserved domains (persistent URLs)
- ✅ Higher rate limits (5,000 req/min)
- ✅ 3 reserved domains (enough for API + UI + testing)
- ✅ No more random URLs on restart

---

## 🔐 Login to Dashboard

### If You Haven't Logged In Yet

1. **Go to:** https://dashboard.ngrok.com
2. **Sign up/Login:**
   - GitHub account
   - Google account
   - Email + password

3. **Get your authtoken:**
   - After login, you'll see your authtoken
   - Copy it

4. **Configure ngrok:**
   ```bash
   ngrok authtoken YOUR_TOKEN_HERE
   ```

---

## 📊 Check Current Usage

### View Usage Statistics

1. Go to: https://dashboard.ngrok.com/observability/event-subscriptions
2. See:
   - Requests per minute
   - Bandwidth usage
   - Active tunnels
   - Connection counts

### Check Rate Limits

Free plan limits:
- 40 connections/minute
- 20 req/sec sustained

If you're hitting these, you'll see "429 Too Many Requests" errors.

---

## 🎨 Features You Get With Paid Account

### Reserved Domains

Never change your URL again!

**Free Plan:**
```
https://random-name-1234.ngrok-free.app  # Changes every restart
```

**Paid Plan:**
```
https://verityngn-api.ngrok.app  # Permanent, never changes
```

### How to Reserve a Domain

1. **Go to:** https://dashboard.ngrok.com/cloud-edge/domains
2. **Click:** "+ New Domain"
3. **Enter:** `verityngn-api` (or your choice)
4. **Save**
5. **Update `.ngrok.yml`:**
   ```yaml
   tunnels:
       verityngn-api:
           domain: verityngn-api.ngrok.app
           proto: http
           addr: 8080
   ```

---

## 🔍 Quick Account Check Commands

```bash
# 1. Check if authenticated
ngrok config check

# 2. View configuration
ngrok config view

# 3. Open dashboard in browser
open https://dashboard.ngrok.com

# 4. Check billing/plan
open https://dashboard.ngrok.com/billing

# 5. View reserved domains (if any)
open https://dashboard.ngrok.com/cloud-edge/domains
```

---

## ✅ Current Status Check

Run these commands to see your current setup:

```bash
# Check ngrok is configured
ngrok config check

# See your version
ngrok version

# Try to view account info (may require dashboard)
open https://dashboard.ngrok.com
```

---

## 🎯 Recommendations

### For Development/Testing
- **Free Plan** is fine if you don't mind changing URLs
- Manually update URLs when ngrok restarts

### For Streamlit Community / Colab Integration
- **Personal Plan ($8/mo)** - Reserve domains so URLs never change
- Update config once, never change it again

### For Production
- **Don't use ngrok** - Deploy to Cloud Run instead
- ngrok is great for development, not production

---

## 📚 Next Steps

1. **Check your plan:**
   ```bash
   open https://dashboard.ngrok.com/billing
   ```

2. **If Free and want to upgrade:**
   - Click "Upgrade" button
   - Choose Personal ($8/mo)
   - Reserve a domain

3. **If already paid:**
   - Reserve domains at: https://dashboard.ngrok.com/cloud-edge/domains
   - Update `.ngrok.yml` with your reserved domain

4. **If staying Free:**
   - Keep using random URLs
   - Update configs after each ngrok restart

---

**Quick Links:**
- 🏠 Dashboard: https://dashboard.ngrok.com
- 💳 Billing: https://dashboard.ngrok.com/billing
- 🌐 Domains: https://dashboard.ngrok.com/cloud-edge/domains
- 📊 Usage: https://dashboard.ngrok.com/observability/event-subscriptions
- 📚 Pricing: https://ngrok.com/pricing

---

**To check now:** Just open https://dashboard.ngrok.com in your browser! 🚀


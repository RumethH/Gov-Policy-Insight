# API Key Management Strategy for Public Demos

This document outlines the architectural and security strategy for managing LLM API keys in a public-facing deployment of the **Gov-Policy-Insight** application, specifically optimized for job application portfolios.

---

## The Challenge

When deploying a portfolio project on AWS EC2 (or any public hosting), we face a conflict between two goals:
1. **Low-Friction User Experience (UX):** Recruiters and hiring managers want a "one-click" demo. Asking them to create, copy, and paste their own Gemini/OpenAI API keys introduces high friction and often leads to them abandoning the demo.
2. **Financial and Operational Security:** Using personal API keys on the backend runs the risk of abuse, scraping, or unexpected billing if the URL is indexed by search engines or shared publicly.

---

## Strategy Options Analysis

### Option 1: Client-Side Keys Only (High Friction)
Users must input their own API key in the UI.
* **Pros:** Zero financial risk to you.
* **Cons:** High user drop-off. Recruiters may not have a key handy or may feel uncomfortable inputting sensitive credentials into a third-party portfolio site.

### Option 2: Backend Keys with No Guardrails (High Risk)
The backend uses your hosted API keys with unrestricted access.
* **Pros:** Perfect "one-click" UX.
* **Cons:** Vulnerable to automated crawlers and billing spikes.

### Option 3: Backend Keys + Cost Guardrails (Standard Production)
The backend uses your keys, but you put strict technical limits in place.
* **Pros:** Excellent UX, controlled risk.
* **Cons:** Requires setup of rate-limiting, daily quotas, or budget alerts.

### Option 4: Dual-Mode / Hybrid (Hiring Portfolio Gold Standard)
The app uses your backend key by default to allow instant testing. It also provides an optional API key input in the UI sidebar. If your backend key runs out of daily budget or gets rate-limited, the UI shows a friendly fallback message prompting the user to supply their own key if they wish to keep exploring.
* **Pros:** Unbeatable UX, resilient to budget outages, demonstrates top-tier production-grade engineering foresight.
* **Cons:** Requires moderate frontend/backend integration.

---

## Recommended Implementation Path (Hybrid Model)

To showcase high production-grade engineering, we can structure the deployment using three layers of defense:

### Layer 1: Front-Door Access Control (Guest Passcode)
Add a simple, single-field password/passcode prompt on the frontend (e.g., passcode: `nsw-policy-demo`). 
* **How it works:** Put this passcode in your GitHub README and on your resume/portfolio site alongside the deployment link. 
* **Value:** This completely blocks automated web crawlers and random scrapers from invoking your LLM while keeping friction for human reviewers extremely low (2 seconds to type).

### Layer 2: API Quotas & Alerts (Provider Side)
Before deploying, set up strict guardrails in your LLM developer console:
* **Google AI Studio (Gemini) / OpenAI Console:** Set hard monthly spend limits (e.g., $5.00 limit) and set up email alerts at 50%, 75%, and 90% usage.
* **Infrastructure Limits:** Because you are deploying to a fixed-size EC2 instance (`t2.micro` or `t3.micro`), your compute will not auto-scale in response to traffic. This acts as a natural hardware bottleneck, preventing massive parallel requests from draining your API budget instantly if scraped by bots.

### Layer 3: UI Optional Override & Graceful Fallback
1. **Optional Sidebar Input:** Add an input field in the Streamlit sidebar: `Google AI API Key (Optional)`.
2. **Pass to Headers:** If provided, store this key in Streamlit's `session_state` and pass it as a custom request header (e.g., `X-Gemini-API-Key`) to your FastAPI backend.
3. **Backend Middleware:** The FastAPI backend checks for the presence of this header:
   * If present: use the user's provided key.
   * If absent: default to the server's environment variable `GOOGLE_API_KEY`.
4. **Friendly Exception Handler:** If any LLM call returns a `QuotaExceeded` or billing error (status 429/402), intercept it and display a polished message in the UI:
   > *"We've hit our daily demo budget cap! To continue exploring the live system, you can optionally paste your own Google Gemini API key in the sidebar."*

---

## Summary
Implementing **Option 4** not only secures your budget but also serves as a strong talking point during job interviews, proving that you design applications with operational budgets, user experience, security, and graceful error handling in mind.

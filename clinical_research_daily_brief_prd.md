# Clinical Research Daily Bri| **F‑1** | Parse the fourteen RSS URLs via `feedparser` at 05:55 CET Mon–Fri. |f — Product Requirements Document (PRD)

## 1. Purpose
Deliver a public web page that shows a tightly curated, daily digest of clinical‑research news. Content is sourced from fourteen open RSS feeds and ranked by an LLM.

## 2. Goals
| Goal | Metric | Target |
|------|--------|--------|
| Surface high‑value items | Avg. LLM score of displayed items | ≥ 4.0 |
| Timely delivery | Brief posted by 06:05 CET Mon–Fri | 99 % |
| Reliability | Feed‑parse failures recovered | ≤ 1 h |
| Usability | Search success rate* | ≥ 90 % |

*Search success = user finds desired article within the first query.

## 3. Scope
**In**: Feed ingestion, ranking, daily brief generation, responsive UI, search/filter, PDF archiving, GitHub Actions automation.  
**Out**: Paywalled feeds, manual editorial review.

## 4. Users & Use Flow
1. Clinical Ops Lead opens the page at work.  
2. Reads the eight–ten headlines, each with a 60‑word summary, 30‑word impact comment, and source link.  
3. Uses the search bar to find “Phase III oncology”.  
4. Downloads the PDF for the compliance archive.

## 5. Functional Requirements

| ID | Requirement |
|----|-------------|
| **F‑1** | Parse the seven RSS URLs via `feedparser` at 05:55 CET Mon–Fri. |
| **F‑2** | For each entry, call the LLM (`temperature 0.3`) → return relevance score 0–5, a 60‑word summary, and a 30‑word impact comment. |
| **F‑3** | Select the top 8–10 items (score ≥ 3; tie‑break by `pubDate`). |
| **F‑4** | Store items in `briefs/YYYY-MM-DD.json`. |
| **F‑5** | Render the web page at `/` showing: title, summary, impact, and “Source” link. |
| **F‑6** | Provide a search bar (full‑text across title, summary, and impact) and dropdown filters for **Source** and preset **Keywords**. Results refresh client‑side. |
| **F‑7** | Generate a PDF (`/briefs/YYYY-MM-DD.pdf`) containing the same items with live links; attach it to the brief record. |
| **F‑8** | Publish the static site and PDFs via GitHub Pages after the workflow run. |
| **F‑9** | Log every feed URL, HTTP status, and parse timestamp for audit. |

## 6. Non‑Functional Requirements
* **Performance:** Page Time to Interactive ≤ 2 s on 3G.  
* **Availability:** 99.8 % (served from GitHub Pages CDN).  
* **Security:** Read‑only site; no auth required. Sanitize all feed input.  
* **Compliance:** Preserve full source links; no content behind paywalls.  
* **Accessibility:** WCAG 2.2 AA (semantic HTML, keyboard navigation, ARIA labels).  
* **Internationalisation:** All dates ISO 8601; UI text English only (v1).

## 7. UX / Visual Guidelines
* Clean, professional aesthetic—white background, 14 px body, 18 px headlines.  
* Card grid ≥ 320 px columns; breaks to a single column on mobile.  
* Each card:
  * Headline (link, bold)  
  * 60‑word summary  
  * 30‑word impact (italic, muted)  
  * Source favicon + domain  
* Sticky header with logo, search bar, and filter icon.  
* Download‑PDF button in the header.  
* Graceful “No results” and error banners.

## 8. Data Model (MVP)
| Field | Type | Notes |
|-------|------|-------|
| `id` | UUID | Feed GUID fallback |
| `title` | string | Raw |
| `summary` | string | LLM 60 words |
| `impact` | string | LLM 30 words |
| `score` | float | 0–5 |
| `source` | enum | One of 14 feeds |
| `pub_date` | datetime | From feed |
| `link` | url | Canonical |
| `brief_date` | date | Run date |

## 9. Architecture & Automation
* **GitHub Actions Workflow**  
  * Cron: `0 5 * * 1-5` (UTC = 06:00 CET).  
  * Steps: Install dependencies → run `pipeline.py` → commit JSON & PDF → deploy.  
* **Backend** (pipeline only)  
  * Python 3.12, `feedparser`, `openai`, `weasyprint`, `jinja2`.  
* **Frontend**  
  * Static HTML, Tailwind CSS, Alpine.js (search/filter).  
* **Hosting:** GitHub Pages.  
* **Logging:** JSON logs in `logs/YYYY-MM-DD.log`; errors trigger GH Actions email.

## 10. Open Issues / Risks
1. Feed outages → fallback cache?  
2. LLM cost spikes → consider local keyword fallback.  
3. PDF size growth → purge after 365 days (not in v1).

## 11. Acceptance Criteria
* **AC‑1**: At 06:05 CET the site shows eight articles from the day’s feeds.  
* **AC‑2**: Every item card ends with “Source: <domain>”.  
* **AC‑3**: Search for “FDA halt” returns matching items in < 300 ms.  
* **AC‑4**: `/briefs/2025-07-07.pdf` downloads a PDF with the same eight items.  
* **AC‑5**: Page layout passes Lighthouse mobile score ≥ 90.

## 12. Timeline
| Phase | Deliverable | Days |
|-------|-------------|------|
| Design | Wireframes, PRD sign‑off | 3 |
| Build | Pipeline, UI, PDF | 7 |
| QA | Functional + performance tests | 3 |
| Launch | Production deploy | 1 |

---


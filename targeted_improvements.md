### Targeted Improvements

| Area | Action | Benefit |
|------|--------|---------|
| **Source acquisition** | • Re‑enable key RSS/Atom feeds (e.g., STAT News AI, Endpoints).<br>• Add Europe PMC, Semantic Scholar, arXiv, medRxiv APIs.<br>• Fetch 403‑blocked pages with Playwright or `requests‑html`. | More sources → higher recall and full‑text access. |
| **Query strategy** | • Rotate baseline keyword sets from MeSH terms.<br>• Paginate Google CSE (start = 1, 11, 21…). | Deeper, broader queries uncover long‑tail items. |
| **Title extraction** | • Drop rules that reject titles with “|”, “–”, “…”.<br>• If metadata scrape fails, keep the raw `<title>` even if short. | Fewer articles discarded as “Untitled”. |
| **Relevance filter** | • Two‑stage screen: quick keyword check, then LLM.<br>• Relax prompt to include NLP and “machine learning” context. | Cuts false negatives; keeps precision. |
| **Ranking** | • Score each item by recency + BM25 match to controlled vocabulary. | Highlights the most relevant articles first. |


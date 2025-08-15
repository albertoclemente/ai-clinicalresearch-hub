# Web App Review & Next Steps

## What Improved ✅
1. **LLM retry loop**  
   You added retries around the summarization step. That reduces random LLM hiccups and gives you more complete briefs when a single call fails.

2. **Ranking logic (recency + relevance)**  
   The scoring/decay for newer items will float fresher news to the top. This makes the page feel alive and saves readers time.

3. **Broader query set**  
   A wider, more targeted topic list will catch more relevant items and reduce “empty” runs.

4. **General structure still good**  
   The separation `FeedProcessor → JSON → SiteGenerator → static HTML` keeps deploys simple and failures contained.

## What Still Needs Work

### 1. HTTP retries + backoff (missing)
If a website is slow or temporarily down, the app just fails. Adding retries for **all** HTTP calls makes the pipeline more resilient.

```python
import time, requests

def http_get(url, params=None, headers=None, timeout=20, max_retries=3):
    for i in range(max_retries):
        try:
            r = requests.get(url, params=params, headers=headers, timeout=timeout)
            if r.status_code in (429, 500, 502, 503, 504):
                wait = int(r.headers.get("Retry-After", 0)) or (2 ** i)
                time.sleep(wait)
                continue
            r.raise_for_status()
            return r
        except requests.RequestException:
            if i == max_retries - 1:
                raise
            time.sleep(2 ** i)
```

---

### 2. Rate limiting/throttling (still naive)
Replace fixed sleeps with a token bucket to prevent 429s.

```python
import time
class Throttle:
    def __init__(self, rate_per_sec=2, burst=4):
        self.tokens = burst
        self.rate = rate_per_sec
        self.last = time.time()
    def consume(self, n=1):
        now = time.time()
        self.tokens = min(self.tokens + (now - self.last)*self.rate, 10)
        self.last = now
        while self.tokens < n:
            time.sleep((n - self.tokens)/self.rate)
            now = time.time()
            self.tokens = min(self.tokens + (now - self.last)*self.rate, 10)
            self.last = now
        self.tokens -= n
```

---

### 3. Deduplication + canonical URLs (missing)
Avoid duplicates by normalizing URLs and hashing titles.

```python
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode
import hashlib

def canonical_url(u:str)->str:
    p = urlparse(u)
    q = [(k,v) for (k,v) in parse_qsl(p.query, keep_blank_values=True)
         if not k.lower().startswith(('utm_', 'fbclid', 'gclid', 'mc_cid','mc_eid'))]
    q.sort()
    p = p._replace(netloc=p.netloc.lower(), query=urlencode(q, doseq=True))
    path = p.path if p.path != '/' else '/'
    if path.endswith('/') and len(path) > 1: path = path[:-1]
    p = p._replace(path=path)
    return urlunparse(p)

seen = set()
unique_entries = []
for e in entries:
    key = (canonical_url(e['url']), hashlib.sha1(e['title'].strip().lower().encode()).hexdigest())
    if key in seen:
        continue
    seen.add(key)
    unique_entries.append(e)
```

---

### 4. Atomic writes (still not there)
Prevent half-written JSON/HTML.

```python
import os
def atomic_write(path, data:bytes):
    tmp = f"{path}.tmp"
    with open(tmp, "wb") as f:
        f.write(data)
    os.replace(tmp, path)
```

---

### 5. Frontend XSS/regex safety (needed)
Escape user input in regex and HTML.

```js
function escapeRegex(s){ return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'); }
function escapeHtml(s){ return s.replace(/[&<>"']/g, m => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m])); }
const safeQuery = escapeRegex(this.searchQuery);
const regex = new RegExp(`(${safeQuery})`, 'gi');
return escapeHtml(text).replace(regex, '<mark class="search-highlight">$1</mark>');
```

Or use `x-text` instead of `x-html` and precompute highlights server-side.

---

### 6. Config & env validation (missing)
Fail fast if keys are missing and pin dependencies.

```python
REQUIRED_ENVS = ["OPENROUTER_API_KEY"]
for v in REQUIRED_ENVS:
    if not os.getenv(v):
        raise RuntimeError(f"Missing env: {v}")
```

---

### 7. Schema validation before write (missing)
Validate entries to avoid bad fields.

```python
from jsonschema import validate

ENTRY_SCHEMA = {
  "type":"object",
  "required":["id","title","url","source","pub_date","summary"],
  "properties":{
    "id":{"type":"string"},
    "title":{"type":"string","minLength":3},
    "url":{"type":"string","format":"uri"},
    "source":{"type":"string"},
    "pub_date":{"type":"string"},
    "summary":{"type":"string"}
  }
}
for e in unique_entries:
    validate(e, ENTRY_SCHEMA)
```

---

### 8. Accessibility (still thin)
Add `aria-label` and live regions.

```html
<input aria-label="Search articles" ...>
<div role="status" aria-live="polite" class="sr-only" x-text="`${filtered.length} results`"></div>
```

---

## Bottom Line
- **Better than before:** yes — LLM retries, broader queries, and ranking help.
- **Not yet robust for unattended daily runs:** fix HTTP retries/backoff, throttle, dedupe/canonicalize, atomic writes, and sanitize the frontend search/highlight.

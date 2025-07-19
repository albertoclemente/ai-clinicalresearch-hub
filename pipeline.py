#!/usr/bin/env python3
"""
AI in Clinical Research Brief Pipeline
Processes RSS feeds, identifies AI-specific content in clinical research, generates HTML.
"""

import json
import logging
import os
import time
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import re
import requests
from urllib.parse import quote_plus

import feedparser
import openai
from bs4 import BeautifulSoup
from jinja2 import Environment, FileSystemLoader
import bleach
from dateutil import parser as date_parser
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class FeedProcessor:
    """Handles web search and AI content identification in clinical research."""
    
    # Base topics for LLM-generated search queries - Comprehensive GenAI in Clinical Trials
    BASE_SEARCH_TOPICS = [
        # Core GenAI Technologies in Clinical Research
        "generative AI in clinical trials",
        "large language models healthcare research",
        "ChatGPT clinical research applications",
        "foundation models drug discovery",
        "synthetic data clinical research",
        
        # Patient-Facing GenAI Applications
        "AI chatbots patient recruitment",
        "conversational AI patient engagement",
        "AI virtual assistants clinical trials",
        "generative AI patient education",
        "AI-powered patient screening",
        
        # Clinical Trial Operations & Management
        "AI protocol writing clinical research",
        "generative AI trial design",
        "AI clinical trial optimization",
        "automated clinical trial monitoring",
        "AI-powered site selection",
        "generative AI regulatory submissions",
        
        # Data & Documentation
        "natural language processing clinical documentation",
        "AI clinical data generation",
        "generative AI medical writing",
        "AI clinical report automation",
        "synthetic clinical trial data",
        "AI clinical data management",
        "generative AI data cleaning",
        "automated clinical data entry",
        "AI clinical database management",
        "AI clinical data integration",
        "generative AI case report forms",
        "automated clinical data validation",
        
        # Safety & Monitoring
        "AI safety monitoring clinical trials",
        "generative AI adverse event reporting",
        "AI pharmacovigilance clinical research",
        "automated safety signal detection",
        
        # Regulatory & Compliance
        "AI regulatory compliance clinical trials",
        "generative AI FDA submissions",
        "AI clinical trial auditing",
        "automated regulatory reporting",
        
        # Analytics & Outcomes
        "generative AI biomarker discovery",
        "AI predictive modeling clinical trials",
        "automated clinical data analysis"
    ]
    
    # Fallback queries if LLM generation fails
    FALLBACK_SEARCH_QUERIES = [
        '"generative AI" "clinical trials" pharmaceutical research',
        '"ChatGPT" "clinical research" drug development study',
        '"large language model" "clinical trials" healthcare research',
        '"synthetic data" "clinical trials" pharmaceutical study',
        '"AI chatbot" "patient recruitment" clinical research',
        '"foundation models" "clinical trials" drug discovery',
        '"generative AI" "protocol writing" clinical research',
        '"LLM" "clinical documentation" pharmaceutical study',
        '"conversational AI" "clinical trials" patient engagement',
        '"generative models" "drug discovery" clinical research'
    ]
    
    # RSS feeds removed - using web search and PubMed only
    RSS_FEEDS = []
    
    # Source-specific limits for content discovery
    SOURCE_LIMITS = {
        'Duke AI Health': 15,               # Duke AI Health (AI focus)
        'STAT AI': 12,                      # STAT AI Coverage
        'MedCity News': 10,                 # MedCity News
        'Google Search': 5,                 # Per search query limit
        'PubMed': 8,                        # Academic papers
        # Default for others: 5
    }
    
    def __init__(self, openai_api_key: str, log_file: str, days_back: int = 30):
        """Initialize the feed processor.
        
        Args:
            openai_api_key: OpenAI API key for content analysis
            log_file: Path to log file
            days_back: Number of days back to consider articles (default: 30)
        """
        self.openai_client = openai.OpenAI(api_key=openai_api_key)
        self.logger = self._setup_logging(log_file)
        self.brief_date = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        self.days_back = days_back
        
        # Initialize search APIs
        self.google_api_key = os.environ.get('GOOGLE_API_KEY')
        self.google_cx = os.environ.get('GOOGLE_CX')  # Custom Search Engine ID
        self.pubmed_base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
        
        # Cache for generated search queries to avoid regenerating on each run
        self._generated_queries_cache = None
        
    def _setup_logging(self, log_file: str) -> logging.Logger:
        """Set up JSON logging as specified in PRD."""
        logger = logging.getLogger('clinical_brief')
        logger.setLevel(logging.INFO)
        
        # Create log directory if it doesn't exist
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        
        handler = logging.FileHandler(log_file)
        formatter = logging.Formatter('%(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def _log_feed_request(self, url: str, status: int, timestamp: str, error: Optional[str] = None):
        """Log feed request details in JSON format."""
        log_entry = {
            "timestamp": timestamp,
            "feed_url": url,
            "http_status": status,
            "error": error
        }
        self.logger.info(json.dumps(log_entry))
    
    def _sanitize_text(self, text: str) -> str:
        """Sanitize and clean text input."""
        if not text:
            return ""
        
        # Handle encoding issues first
        if isinstance(text, bytes):
            text = text.decode('utf-8', errors='replace')
        
        # Replace common problematic characters
        text = text.replace('\u2013', '-')  # en dash
        text = text.replace('\u2014', '--')  # em dash
        text = text.replace('\u2018', "'")  # left single quote
        text = text.replace('\u2019', "'")  # right single quote
        text = text.replace('\u201c', '"')  # left double quote
        text = text.replace('\u201d', '"')  # right double quote
        text = text.replace('\u2026', '...')  # ellipsis
        text = text.replace('\u00a0', ' ')  # non-breaking space
        text = text.replace('\ufeff', '')  # BOM (byte order mark)
        
        # Remove HTML tags and entities
        clean_text = bleach.clean(text, tags=[], strip=True)
        
        # Normalize whitespace
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
        
        # Ensure only printable ASCII and common Unicode characters
        clean_text = ''.join(char for char in clean_text if ord(char) < 127 or char in 'áéíóúàèìòùâêîôûäëïöüñç')
        
        return clean_text
    
    def _extract_title_from_webpage(self, url: str) -> str:
        """Extract the actual title from a webpage by scraping it."""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Handle encoding properly
            response.encoding = response.apparent_encoding
            content = response.text.encode('utf-8', errors='replace').decode('utf-8')
            
            soup = BeautifulSoup(content, 'html.parser')
            
            # Try multiple title extraction methods in order of preference
            title_sources = [
                ('og:title', soup.find('meta', {'property': 'og:title'})),
                ('twitter:title', soup.find('meta', {'name': 'twitter:title'})),
                ('citation_title', soup.find('meta', {'name': 'citation_title'})),  # Academic papers
                ('dc.title', soup.find('meta', {'name': 'dc.title'})),        # Dublin Core
                ('article:title', soup.find('meta', {'property': 'article:title'})),
                ('title_tag', soup.find('title')),
                ('h1_tag', soup.find('h1')),
                ('h2_tag', soup.find('h2')),  # Sometimes the main title is in h2
            ]
            
            def is_scraped_title_valid(title: str, source_type: str) -> bool:
                """Validate scraped title quality."""
                if not title or len(title.strip()) < 15:
                    return False
                
                title_lower = title.lower()
                
                # More aggressive filtering for scraped content
                invalid_patterns = [
                    'latest research and news',
                    'health sciences - latest',
                    'nature medicine',
                    'nature - international',
                    'arxiv.org',
                    'pubmed',
                    'ncbi',
                    'coming soon',
                    'page not found',
                    '404 error',
                    'access denied',
                    'untitled',
                    'home page',
                    'main page',
                    'latest news',
                    'breaking news',
                    'health news',
                    'medical news',
                    'error 404',
                    'not found',
                    'forbidden',
                    'access restricted'
                ]
                
                for pattern in invalid_patterns:
                    if pattern in title_lower:
                        return False
                
                # Reject titles that are just site names or navigation
                if title_lower in ['nature', 'science', 'plos', 'bmj', 'nejm', 'jama', 'arxiv', 'pubmed']:
                    return False
                
                # Reject titles with typical truncation patterns
                if '|' in title:
                    parts = title.split('|')
                    if len(parts) > 1:
                        last_part = parts[-1].strip()
                        if len(last_part) <= 3 or last_part.lower() in ['s', 'n', 'nature', 'nat', 'sci', 'bmj', 'nejm']:
                            return False
                
                # Additional validation for title tag content
                if source_type == 'title_tag':
                    # Title tags often contain site name, try to extract just the article title
                    separators = [' | ', ' - ', ' :: ', ' > ', ' — ']
                    for sep in separators:
                        if sep in title:
                            parts = title.split(sep)
                            # Take the longest meaningful part
                            main_part = max(parts, key=len).strip()
                            if len(main_part) >= 20 and not any(pattern in main_part.lower() for pattern in invalid_patterns):
                                return main_part == title or len(main_part) > len(title) * 0.6
                
                return True
            
            for source_name, source in title_sources:
                if source:
                    if source.name == 'meta':
                        title = source.get('content', '')
                    else:
                        title = source.get_text(strip=True)
                    
                    # Clean and validate title
                    if title:
                        title = self._sanitize_text(title)
                        
                        # For title tags, try to extract the main article title
                        if source_name == 'title_tag' and ('|' in title or '-' in title or '::' in title):
                            separators = [' | ', ' - ', ' :: ', ' > ', ' — ', ' – ']
                            for sep in separators:
                                if sep in title:
                                    parts = [part.strip() for part in title.split(sep)]
                                    # Find the part that looks most like an article title
                                    for part in sorted(parts, key=len, reverse=True):
                                        if len(part) >= 20 and is_scraped_title_valid(part, source_name):
                                            return part
                        
                        if is_scraped_title_valid(title, source_name):
                            return title
            
        except Exception as e:
            self.logger.warning(json.dumps({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "error": f"Failed to extract title from {url}: {str(e)}",
                "url": url
            }))
        
        return ""

    def generate_search_queries(self) -> List[str]:
        """Generate optimized search queries using LLM for better content discovery."""
        # Return cached queries if available
        if self._generated_queries_cache:
            return self._generated_queries_cache
        
        try:
            prompt = f"""
            You are a search query optimization expert specializing in clinical research and AI technology. 
            Generate 10 highly effective Google search queries to find recent articles about Generative AI applications across ALL AREAS of clinical trials and clinical research.

            REQUIREMENTS:
            1. Keep queries SIMPLE and BROAD enough to find results
            2. Target SPECIFIC AI technologies: ChatGPT, GPT-4, Claude, Llama, foundation models, LLMs
            3. Focus EXCLUSIVELY on clinical trials and clinical research operations
            4. Use quotation marks sparingly - only for 2-3 word exact phrases
            5. Mix brand names, technology types, and clinical trial applications
            6. Each query should be 3-8 words for optimal Google search performance
            7. Avoid complex boolean operators that might limit results

            FOCUS ON CLINICAL TRIAL OPERATIONS ONLY:
            {', '.join(self.BASE_SEARCH_TOPICS)}

            EFFECTIVE QUERY EXAMPLES (CLINICAL TRIALS FOCUSED):
            ChatGPT clinical trials
            "AI chatbot" patient recruitment
            LLM trial protocol
            generative AI clinical study
            AI trial monitoring
            synthetic data clinical trials
            AI clinical research
            
            Generate queries that target CLINICAL TRIAL OPERATIONS specifically:
            - Patient recruitment and enrollment for trials
            - Clinical trial protocol development
            - Trial data management and analysis
            - Clinical trial monitoring and compliance
            - Regulatory submissions for trials
            - Clinical research documentation
            - Trial site management and operations
            - Clinical study optimization

            CRITICAL: All queries must include "clinical trials", "clinical research", "clinical study", 
            or similar trial-specific terms. Avoid general healthcare AI applications.
            
            Return ONLY the search queries, one per line, no numbering or explanations.
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,  # Higher temperature for more creative/diverse queries
                max_tokens=400
            )
            
            content = response.choices[0].message.content.strip()
            
            # Parse queries from response
            queries = []
            for line in content.split('\n'):
                line = line.strip()
                # Remove numbering, bullets, or other formatting
                line = re.sub(r'^[\d\.\-\*\•]\s*', '', line)
                if line and len(line) > 10:  # Ensure meaningful queries
                    queries.append(line)
            
            # Validate we got enough queries
            if len(queries) >= 5:
                self._generated_queries_cache = queries[:10]  # Limit to 10 queries
                
                self.logger.info(json.dumps({
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "llm_generated_queries": len(self._generated_queries_cache),
                    "queries": self._generated_queries_cache
                }))
                
                return self._generated_queries_cache
            else:
                self.logger.warning(f"LLM generated only {len(queries)} queries, using fallback")
                
        except Exception as e:
            self.logger.error(json.dumps({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "error": f"Failed to generate search queries with LLM: {str(e)}",
                "fallback": "using predefined queries"
            }))
        
        # Fallback to predefined queries
        self._generated_queries_cache = self.FALLBACK_SEARCH_QUERIES
        return self._generated_queries_cache

    def refresh_search_queries(self) -> List[str]:
        """Force regeneration of search queries, bypassing cache."""
        self._generated_queries_cache = None
        return self.generate_search_queries()

    def _extract_full_title(self, item: Dict) -> str:
        """Extract full title from Google search result, trying multiple sources."""
        
        def is_valid_title(title: str) -> bool:
            """Check if a title is valid and not generic/truncated."""
            if not title or len(title.strip()) < 20:  # Increased minimum length
                return False
            
            title_lower = title.lower()
            
            # Reject generic/placeholder titles
            generic_patterns = [
                'latest research and news',
                'health sciences - latest',
                'health sciences articles',
                'nature medicine',
                'arxiv.org',
                'pubmed',
                'ncbi',
                'coming soon',
                'page not found',
                '404 error',
                'access denied',
                'untitled',
                'home page',
                'main page',
                'latest news',
                'breaking news',
                'health news',
                'medical news',
                'research | nejm',
                'articles from across',
                'view all articles',
                'browse articles',
                'browse all',
                'view articles',
                'view all',
                'news & comment',
                'news and comment',
                'browse by',
                'filter by',
                'search results',
                'table of contents',
                'current issue',
                'nature portfolio',
                'journal of medical internet research',
                'jmir - journal',
                '| nature medicine',
                'news & comment |',
                'comment | nature',
                'health forum',
                'jama health forum',
                'health sciences |',
                '| nature communications',
                'nature communications',
                '| nature',
                'nature |',
                'sales & marketing',
                'sales and marketing',
                'marketing |',
                '| marketing',
                'connecting with physicians',
                'connecting with patients'
            ]
            
            for pattern in generic_patterns:
                if pattern in title_lower:
                    return False
            
            # Reject truncated titles (ending with | followed by short text)
            if '|' in title:
                parts = title.split('|')
                if len(parts) > 1:
                    # If the part after | is very short, it's likely truncated
                    last_part = parts[-1].strip()
                    if len(last_part) <= 5 or last_part.lower() in ['s', 'n', 'nature', 'nat', 'sci', 'nejm', 'ai']:
                        return False
                    # Check if it's a generic site name
                    if last_part.lower() in ['nature', 'science', 'plos', 'bmj', 'nejm', 'jama', 'nejm ai']:
                        return False
            
            # Reject titles that are just ellipsis or very short
            if title.strip().endswith('...') or title.strip().endswith('…'):
                return False
            
            # Reject titles with excessive truncation indicators
            if title.count('...') > 1 or title.count('…') > 1:
                return False
            
            return True
        
        # Try different title sources in order of preference
        title_sources = [
            ('google_title', item.get('title', '')),
            ('og_title', item.get('pagemap', {}).get('metatags', [{}])[0].get('og:title', '')),
            ('twitter_title', item.get('pagemap', {}).get('metatags', [{}])[0].get('twitter:title', '')),
            ('article_headline', item.get('pagemap', {}).get('article', [{}])[0].get('headline', '')),
            ('citation_title', item.get('pagemap', {}).get('metatags', [{}])[0].get('citation_title', '')),
        ]
        
        # First pass: try to find a good title from metadata
        for source_name, title in title_sources:
            if title:
                clean_title = self._sanitize_text(title)
                if is_valid_title(clean_title):
                    return clean_title
        
        # Second pass: try scraping the webpage if no good title found
        link = item.get('link', '')
        if link:
            scraped_title = self._extract_title_from_webpage(link)
            if scraped_title and is_valid_title(scraped_title):
                return scraped_title
        
        # Last resort: use the first available title but mark it as potentially problematic
        for source_name, title in title_sources:
            if title:
                clean_title = self._sanitize_text(title)
                if clean_title and len(clean_title.strip()) >= 10:
                    # Check if this would be a problematic title
                    if (clean_title.endswith('...') or clean_title.endswith('…') or
                        '...' in clean_title or '…' in clean_title or
                        len(clean_title) < 25 or  # Very short titles are often truncated
                        clean_title.lower().endswith(' |') or
                        clean_title.count('.') > 5):  # Titles with too many dots are often malformed
                        continue  # Skip this source, try the next one
                    
                    # Log this as a problematic title for debugging
                    self.logger.warning(json.dumps({
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "issue": "using_potentially_bad_title",
                        "title": clean_title,
                        "url": link,
                        "source": source_name
                    }))
                    return clean_title
        
        return "Untitled Article"

    def search_google(self, query: str, max_results: int = 5) -> List[Dict]:
        """Search Google for articles using Custom Search API."""
        if not self.google_api_key or not self.google_cx:
            self.logger.warning("Google API credentials not found. Skipping Google search.")
            return []
        
        entries = []
        try:
            # Calculate date range for recent articles
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=self.days_back)
            
            # Use the query directly without domain restrictions to get broader coverage
            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                'key': self.google_api_key,
                'cx': self.google_cx,
                'q': query,
                'num': min(max_results, 10),  # Max 10 per request
                'sort': 'date',  # Sort by date
                'dateRestrict': f'd{self.days_back}',  # Restrict to last N days
                'gl': 'us',  # Geographic location
                'lr': 'lang_en',  # Language restriction
                'safe': 'off',  # Don't filter results
                'filter': '1',  # Enable duplicate filtering
            }
            
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            for item in data.get('items', []):
                # Skip general job sites, career pages, and irrelevant domains
                link = item.get('link', '')
                if any(domain in link.lower() for domain in [
                    'linkedin.com', 'indeed.com', 'glassdoor.com', 'jobs.',
                    'career', 'wikipedia.org', 'youtube.com', 'twitter.com',
                    'facebook.com', 'reddit.com'
                ]):
                    continue
                
                title = self._extract_full_title(item)
                
                # Skip if we couldn't get a good title
                if title == "Untitled Article" or not title:
                    continue
                
                # Skip if title is too generic or contains job-related keywords
                if any(keyword in title.lower() for keyword in [
                    'job', 'career', 'hiring', 'position', 'vacancy',
                    'employment', 'recruiter', 'hr ', 'human resources',
                    'latest research and news', 'health sciences - latest'
                ]):
                    continue
                
                # Enhanced filtering for navigation/category pages
                if any(nav_pattern in title.lower() for nav_pattern in [
                    'browse articles', 'browse all', 'view articles', 'view all',
                    'news & comment', 'news and comment', 'latest news',
                    'research |', '| research', 'articles |', '| articles',
                    'health sciences articles', 'latest research and news',
                    'home page', 'main page', 'category:', 'section:',
                    '- journal of', 'journal of medical internet research',
                    'nature portfolio', 'nature medicine |', 'nejm ai |',
                    'browse by', 'filter by', 'search results',
                    'table of contents', 'current issue',
                    '| nature medicine', 'comment | nature', 'health forum',
                    'jama health forum', 'jama network', 'health sciences |',
                    '| nature communications', 'nature communications',
                    '| nature', 'nature |', 'sales & marketing',
                    'sales and marketing', 'marketing |', '| marketing',
                    'connecting with physicians', 'connecting with patients'
                ]):
                    continue
                
                entry_data = {
                    'id': str(uuid.uuid4()),
                    'title': title,
                    'description': self._sanitize_text(item.get('snippet', '')),
                    'link': link,
                    'pub_date': self._parse_date(item.get('pagemap', {}).get('metatags', [{}])[0].get('article:published_time', '')),
                    'source': self._extract_domain(link),
                    'brief_date': self.brief_date,
                    'search_query': query
                }
                
                if entry_data['title'] and entry_data['link']:
                    entries.append(entry_data)
            
            self.logger.info(json.dumps({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "search_type": "google",
                "query": query,
                "results_found": len(entries),
                "max_requested": max_results
            }))
            
        except Exception as e:
            self.logger.error(json.dumps({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "search_type": "google",
                "query": query,
                "error": str(e)
            }))
        
        return entries
    
    def search_pubmed(self, query: str, max_results: int = 8) -> List[Dict]:
        """Search PubMed for recent research papers."""
        entries = []
        try:
            # Calculate date range
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=self.days_back)
            
            # Search PubMed
            search_url = f"{self.pubmed_base_url}esearch.fcgi"
            search_params = {
                'db': 'pubmed',
                'term': f'{query} AND ("{start_date.strftime("%Y/%m/%d")}"[Date - Publication] : "{end_date.strftime("%Y/%m/%d")}"[Date - Publication])',
                'retmax': max_results,
                'sort': 'date',
                'retmode': 'json'
            }
            
            search_response = requests.get(search_url, params=search_params, timeout=30)
            search_response.raise_for_status()
            search_data = search_response.json()
            
            pmids = search_data.get('esearchresult', {}).get('idlist', [])
            
            if pmids:
                # Fetch details for found papers
                fetch_url = f"{self.pubmed_base_url}esummary.fcgi"
                fetch_params = {
                    'db': 'pubmed',
                    'id': ','.join(pmids),
                    'retmode': 'json'
                }
                
                fetch_response = requests.get(fetch_url, params=fetch_params, timeout=30)
                fetch_response.raise_for_status()
                fetch_data = fetch_response.json()
                
                for pmid, paper in fetch_data.get('result', {}).items():
                    if pmid == 'uids':
                        continue
                    
                    entry_data = {
                        'id': str(uuid.uuid4()),
                        'title': self._sanitize_text(paper.get('title', '')),
                        'description': self._sanitize_text(paper.get('title', '') + ' - ' + str(paper.get('authors', ''))),
                        'link': f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                        'pub_date': self._parse_pubmed_date(paper.get('pubdate', '')),
                        'source': 'PubMed',
                        'brief_date': self.brief_date,
                        'search_query': query
                    }
                    
                    if entry_data['title'] and entry_data['link']:
                        entries.append(entry_data)
            
            self.logger.info(json.dumps({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "search_type": "pubmed",
                "query": query,
                "results_found": len(entries),
                "max_requested": max_results
            }))
            
        except Exception as e:
            self.logger.error(json.dumps({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "search_type": "pubmed",
                "query": query,
                "error": str(e)
            }))
        
        return entries
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain name from URL for source identification."""
        try:
            from urllib.parse import urlparse
            domain = urlparse(url).netloc
            # Clean up domain (remove www, etc.)
            if domain.startswith('www.'):
                domain = domain[4:]
            return domain.title()
        except:
            return 'Unknown'
    
    def _parse_pubmed_date(self, date_str: str) -> str:
        """Parse PubMed date format."""
        if not date_str:
            return datetime.now(timezone.utc).isoformat()
        
        try:
            # PubMed dates are often in format "2024 Jul 15" or "2024 Jul"
            if len(date_str.split()) >= 2:
                # Try to parse with day
                try:
                    parsed_date = datetime.strptime(date_str, '%Y %b %d')
                except:
                    # Try to parse without day
                    parsed_date = datetime.strptime(date_str, '%Y %b')
                return parsed_date.replace(tzinfo=timezone.utc).isoformat()
        except:
            pass
        
        return datetime.now(timezone.utc).isoformat()
    
    def fetch_feeds(self, default_max: int = 5) -> List[Dict]:
        """Fetch articles using web search APIs only (no RSS feeds)."""
        all_entries = []
        total_fetched = 0
        
        self.logger.info(json.dumps({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "days_back": self.days_back,
            "message": f"Fetching articles from the last {self.days_back} days using web search APIs only"
        }))
        
        # Phase 1: Web Search (Primary source)
        if self.google_api_key and self.google_cx:
            print("Generating optimized search queries with LLM...")
            search_queries = self.generate_search_queries()
            print(f"Generated {len(search_queries)} search queries")
            
            print("Searching web for Generative AI content...")
            for query in search_queries:
                max_results = self.SOURCE_LIMITS.get('Google Search', default_max)
                entries = self.search_google(query, max_results)
                all_entries.extend(entries)
                total_fetched += len(entries)
                
                # Add small delay to respect API limits
                time.sleep(0.1)
        else:
            print("Google API not configured. Skipping web search.")
        
        # Phase 2: PubMed Search (Academic papers) - Clinical Trials Focus
        print("Searching PubMed for clinical trials research papers...")
        pubmed_queries = [
            "generative AI clinical trials",
            "large language model clinical trials",
            "ChatGPT clinical trials",
            "AI chatbot patient recruitment clinical trials",
            "artificial intelligence clinical trial design",
            "AI clinical trial monitoring",
            "synthetic data clinical trials",
            "natural language processing clinical trial data",
            "AI clinical trial automation",
            "generative AI clinical research protocol"
        ]
        
        for query in pubmed_queries:
            max_results = self.SOURCE_LIMITS.get('PubMed', default_max)
            entries = self.search_pubmed(query, max_results)
            all_entries.extend(entries)
            total_fetched += len(entries)
        
        # Remove duplicates based on URL
        unique_entries = []
        seen_urls = set()
        for entry in all_entries:
            if entry['link'] not in seen_urls:
                seen_urls.add(entry['link'])
                unique_entries.append(entry)
        
        self.logger.info(json.dumps({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_articles_fetched": len(unique_entries),
            "duplicates_removed": len(all_entries) - len(unique_entries),
            "search_queries_used": len(search_queries) if 'search_queries' in locals() else len(self.FALLBACK_SEARCH_QUERIES),
            "search_apis_used": 2,  # Google + PubMed
            "llm_query_generation": self._generated_queries_cache is not None
        }))
                
        return unique_entries
    
    def _parse_date(self, date_str: str) -> str:
        """Parse and normalize publication date."""
        if not date_str:
            return datetime.now(timezone.utc).isoformat()
        
        try:
            parsed_date = date_parser.parse(date_str)
            return parsed_date.isoformat()
        except:
            return datetime.now(timezone.utc).isoformat()
    
    def _get_source_name(self, feed_url: str) -> str:
        """Extract source name from feed URL."""
        source_mapping = {
            'aihealth.duke.edu': 'Duke AI Health',
            'statnews.com/tag/artificial-intelligence': 'STAT AI',
            'medcitynews.com': 'MedCity News',
        }
        
        for domain, name in source_mapping.items():
            if domain in feed_url:
                return name
        
        return 'Unknown'
    
    def identify_ai_content(self, entries: List[Dict]) -> List[Dict]:
        """Identify articles specifically about AI applications in clinical research and tag them using OpenAI API."""
        ai_entries = []
        
        for entry in entries:
            # Try up to 3 times to ensure we get all required fields
            for attempt in range(3):
                try:
                    prompt = f"""
                    You are a STRICT Generative AI and clinical trials expert. You must be HIGHLY SELECTIVE and only classify articles as AI-related if they EXPLICITLY mention specific AI technologies in clinical research contexts.

                    STRICT CRITERIA - MUST EXPLICITLY MENTION CLINICAL TRIALS OR CLINICAL RESEARCH OPERATIONS:
                    
                    TIER 1 - GENERATIVE AI IN CLINICAL TRIALS (HIGHEST PRIORITY):
                    - Large Language Models (LLMs): ChatGPT, GPT-4, Claude, Llama, Gemini used in clinical trial operations
                    - AI chatbots for patient recruitment, enrollment, or trial engagement
                    - AI-powered protocol writing, trial design, or regulatory submissions
                    - Synthetic data generation specifically for clinical trials
                    - Natural language generation for clinical trial documentation
                    - AI scribes or documentation tools used in clinical research settings
                    
                    TIER 2 - APPLIED AI IN CLINICAL TRIAL OPERATIONS:
                    - Natural language processing for clinical trial data analysis
                    - AI tools for clinical trial monitoring or safety assessment
                    - AI-powered patient stratification or recruitment in trials
                    
                    REJECT IMMEDIATELY IF:
                    - General healthcare AI without clinical trial connection
                    - Medical education or training (unless specifically for clinical trials)
                    - Diagnostic AI tools (unless part of clinical trial operations)
                    - General patient care AI (unless in trial context)
                    - Research methodology reviews (unless about trial operations)
                    - Healthcare system improvements (unless trial-specific)
                    - Academic surveys or reviews without trial focus
                    - AI ethics or explainability (unless trial-specific)
                    
                    CLINICAL TRIAL KEYWORDS REQUIRED:
                    Must mention: "clinical trial", "clinical research", "trial design", "patient recruitment", 
                    "trial protocol", "clinical study", "trial monitoring", "trial operations", "trial data",
                    "regulatory compliance", "trial management", "clinical investigation"
                    
                    Article Title: {entry['title']}
                    Article Description: {entry['description'][:500]}
                    
                    CRITICAL ANALYSIS: 
                    1. Does this article EXPLICITLY mention clinical trials or clinical research operations?
                    2. Is the AI technology being used specifically in trial contexts (not general healthcare)?
                    3. Does this discuss actual trial operations like recruitment, monitoring, data collection, or compliance?
                    
                    BE EXTREMELY STRICT: Only classify as AI-related if the article specifically discusses AI applications 
                    in clinical trial operations, not general healthcare AI applications.

                    You MUST provide ALL FIVE fields:
                    1. is_ai_related: true/false (BE STRICT - only true for explicit AI technology mentions)
                    2. A 50-word summary of the SPECIFIC AI technology mentioned
                    3. A 120-word INSIGHTFUL comment analyzing THIS SPECIFIC article's implications for clinical trials (be unique, detailed, and article-specific - avoid generic statements)
                    4. Resources (2-3 specific GenAI clinical trial resources)
                    5. ai_tag: Choose the most specific category

                    For RESOURCES, use these templates:
                    • PubMed search for 'generative AI clinical trials': https://pubmed.ncbi.nlm.nih.gov/?term=generative+AI+clinical+trials
                    • FDA guidance on AI in clinical trials: https://www.fda.gov/regulatory-information/search-fda-guidance-documents/artificial-intelligence-and-machine-learning-software-medical-device
                    • Clinical Trials Transformation Initiative AI resources: https://www.ctti-clinicaltrials.org/

                    JSON format required:
                    {{
                        "is_ai_related": true/false,
                        "summary": "50-word summary of SPECIFIC AI technology mentioned",
                        "comment": "120-word VARIED and UNIQUE analysis of THIS specific article's clinical trial implications. START WITH DIFFERENT PHRASES - avoid 'This article highlights' or 'This study'. Use varied openings like: 'The implementation of...', 'By leveraging...', 'Research demonstrates...', 'The application reveals...', 'Findings suggest...', 'Evidence indicates...'. Analyze the specific AI application, potential impact on trial phases, operational benefits, challenges, regulatory considerations, and implementation feasibility.",
                        "resources": "2-3 resources in bullet format",
                        "ai_tag": "Most specific category from: Generative AI, Natural Language Processing, Trial Optimization, AI Ethics"
                    }}
                    """
                    
                    response = self.openai_client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.3,
                        max_tokens=500
                    )
                    
                    # Parse the JSON response
                    content = response.choices[0].message.content.strip()
                    
                    # Debug: Log the raw response
                    self.logger.info(json.dumps({
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "entry_id": entry['id'],
                        "entry_title": entry['title'][:50],
                        "raw_llm_response": content[:200],
                        "attempt": attempt + 1
                    }))
                    
                    # Extract JSON from response
                    json_match = re.search(r'\{.*\}', content, re.DOTALL)
                    if json_match:
                        result = json.loads(json_match.group())
                        
                        # Debug: Log the parsed result
                        self.logger.info(json.dumps({
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            "entry_id": entry['id'],
                            "parsed_result": result,
                            "is_ai_related": result.get('is_ai_related', False)
                        }))
                        
                        # Validate all required fields are present and valid
                        if self._validate_ai_response(result):
                            # Only include AI-related articles
                            if result.get('is_ai_related', False):
                                entry['is_ai_related'] = True
                                entry['summary'] = self._sanitize_text(result.get('summary', ''))
                                entry['comment'] = self._sanitize_text(result.get('comment', ''))
                                entry['resources'] = self._sanitize_text(result.get('resources', ''))
                                entry['ai_tag'] = self._sanitize_text(result.get('ai_tag', 'AI Research'))
                                
                                # Ensure word limits
                                entry['summary'] = self._limit_words(entry['summary'], 60)
                                entry['comment'] = self._limit_words(entry['comment'], 140)  # Increased for detailed insights
                                entry['resources'] = self._limit_words(entry['resources'], 120)  # Increased for URLs and descriptions
                                
                                ai_entries.append(entry)
                            break  # Success, break out of retry loop
                        else:
                            self.logger.warning(f"Invalid LLM response for entry {entry['id']}, attempt {attempt + 1}: {result}")
                            if attempt == 2:  # Last attempt
                                self.logger.error(f"Failed to get valid LLM response for entry {entry['id']} after 3 attempts")
                    else:
                        self.logger.warning(f"No JSON found in LLM response for entry {entry['id']}, attempt {attempt + 1}")
                        if attempt == 2:  # Last attempt
                            self.logger.error(f"Failed to extract JSON from LLM response for entry {entry['id']} after 3 attempts")
                
                except Exception as e:
                    self.logger.error(f"Error processing entry {entry['id']}, attempt {attempt + 1}: {str(e)}")
                    if attempt == 2:  # Last attempt
                        continue
        
        return ai_entries
    
    def _validate_ai_response(self, result: Dict) -> bool:
        """Validate that LLM response contains all required fields for AI identification."""
        required_fields = ['is_ai_related', 'summary', 'comment', 'resources', 'ai_tag']
        
        for field in required_fields:
            if field not in result:
                return False
            
            value = result[field]
            
            # Validate is_ai_related
            if field == 'is_ai_related':
                if not isinstance(value, bool):
                    return False
            
            # For non-AI articles, we don't need complete resources and ai_tag
            elif field in ['summary', 'comment']:
                if not isinstance(value, str) or len(value.strip()) < 5:
                    return False
            
            # For AI-related articles, require complete ai_tag
            elif field == 'ai_tag':
                if result.get('is_ai_related', False):
                    if not isinstance(value, str) or len(value.strip()) < 5:
                        return False
                # For non-AI articles, ai_tag can be empty
            
            # Validate resources field (can be string or list)
            elif field == 'resources':
                if result.get('is_ai_related', False):
                    # For AI articles, require resources
                    if isinstance(value, list):
                        if len(value) == 0:
                            return False
                        result[field] = '\n'.join(value)
                    elif isinstance(value, str):
                        if len(value.strip()) < 5:
                            return False
                    else:
                        return False
                else:
                    # For non-AI articles, resources can be empty
                    if isinstance(value, list):
                        result[field] = '\n'.join(value) if value else ""
                    elif not isinstance(value, str):
                        return False
        
        return True
    
    def _limit_words(self, text: str, max_words: int) -> str:
        """Limit text to specified number of words with smarter truncation."""
        words = text.split()
        if len(words) > max_words:
            # Try to find a sentence-ending punctuation within the last few words
            # to avoid cutting off mid-thought
            truncated_text = ' '.join(words[:max_words])
            
            # If we already have a complete sentence, we're good
            if truncated_text.rstrip().endswith(('.', '!', '?')):
                return truncated_text
                
            # Otherwise check if there's a sentence break in the last 15 words
            last_sentence_break = max(
                truncated_text.rfind('.'), 
                truncated_text.rfind('!'),
                truncated_text.rfind('?')
            )
            
            if last_sentence_break > len(truncated_text) - 30:
                # Found a recent sentence break, use it
                return truncated_text[:last_sentence_break + 1]
            
            # No good break point found, add ellipsis
            return truncated_text + '...'
            
        return text
    
    def select_articles(self, entries: List[Dict]) -> List[Dict]:
        """Select and sort AI-specific clinical research articles by publication date."""
        # Sort by publication date (descending) to show newest first
        sorted_entries = sorted(
            entries,
            key=lambda x: x.get('pub_date', ''),
            reverse=True
        )
        
        # Return all AI-specific articles (already filtered in identify_ai_content)
        return sorted_entries
    
    def save_brief_data(self, entries: List[Dict], output_file: str):
        """Save brief data to JSON file."""
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        
        brief_data = {
            'brief_date': self.brief_date,
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'items': entries,
            'total_items': len(entries)
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(brief_data, f, indent=2, ensure_ascii=False)


class SiteGenerator:
    """Handles HTML generation using Jinja2."""
    
    def __init__(self, templates_dir: str = "templates"):
        """Initialize the site generator."""
        self.env = Environment(loader=FileSystemLoader(templates_dir))
        
    def generate_html(self, brief_data: Dict, output_file: str):
        """Generate HTML page using Jinja2 template."""
        template = self.env.get_template('index.html')
        
        # Prepare template context
        context = {
            'brief_date': brief_data['brief_date'],
            'generated_at': brief_data['generated_at'],
            'items': brief_data['items'],
            'total_items': brief_data['total_items']
        }
        
        # Render template
        html_content = template.render(**context)
        
        # Save HTML file
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)


def main():
    """Main pipeline execution."""
    # Configuration
    openai_api_key = os.environ.get('OPENAI_API_KEY')
    if not openai_api_key:
        raise ValueError("OPENAI_API_KEY environment variable is required")
    
    # Configuration: Default max entries for sources without specific limits
    default_max_entries = int(os.environ.get('DEFAULT_MAX_ENTRIES', '8'))
    
    # Configuration: Timeframe for article collection (configurable via environment)
    days_back = int(os.environ.get('DAYS_BACK', '30'))  # Default to 30 days
    
    brief_date = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    log_file = f"logs/{brief_date}.log"
    json_file = f"briefs/{brief_date}.json"
    html_file = "site/index.html"
    
    # Initialize processors
    feed_processor = FeedProcessor(openai_api_key, log_file, days_back)
    site_generator = SiteGenerator()
    
    print(f"Starting AI in Clinical Research Brief pipeline for {brief_date}")
    print(f"Collecting articles from the last {days_back} days")
    
    # Step 1: Fetch feeds using web search APIs only
    print("Fetching articles using web search APIs (no RSS)...")
    entries = feed_processor.fetch_feeds(default_max=default_max_entries)
    print(f"Fetched {len(entries)} entries from web search APIs")
    
    # Step 2: Identify AI-specific content in clinical research
    print("Identifying AI-specific articles in clinical research with OpenAI...")
    ai_entries = feed_processor.identify_ai_content(entries)
    print(f"Identified {len(ai_entries)} AI-specific clinical research articles")
    
    # Step 3: Select and sort articles
    print("Selecting and sorting articles...")
    selected_articles = feed_processor.select_articles(ai_entries)
    print(f"Selected {len(selected_articles)} articles for the brief")
    
    # Step 4: Save brief data
    print("Saving brief data...")
    feed_processor.save_brief_data(selected_articles, json_file)
    
    # Step 5: Generate HTML
    print("Generating HTML...")
    with open(json_file, 'r', encoding='utf-8') as f:
        brief_data = json.load(f)
    site_generator.generate_html(brief_data, html_file)
    
    print(f"Pipeline completed successfully!")
    print(f"- Brief data: {json_file}")
    print(f"- HTML page: {html_file}")
    print(f"- Logs: {log_file}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
AI in Clinical Research Brief Pipeline
Processes RSS feeds, identifies AI-specific content in clinical research, generates HTML and PDF output.
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
    
    # Highly targeted search queries for Generative AI in clinical trials
    SEARCH_QUERIES = [
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
        
        # Remove HTML tags and entities
        clean_text = bleach.clean(text, tags=[], strip=True)
        
        # Normalize whitespace
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
        
        return clean_text
    
    def _extract_title_from_webpage(self, url: str) -> str:
        """Extract the actual title from a webpage by scraping it."""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Try multiple title extraction methods in order of preference
            title_sources = [
                soup.find('meta', {'property': 'og:title'}),
                soup.find('meta', {'name': 'twitter:title'}),
                soup.find('meta', {'name': 'citation_title'}),  # Academic papers
                soup.find('meta', {'name': 'dc.title'}),        # Dublin Core
                soup.find('title'),
                soup.find('h1'),
                soup.find('h2'),  # Sometimes the main title is in h2
            ]
            
            for source in title_sources:
                if source:
                    if source.name == 'meta':
                        title = source.get('content', '')
                    else:
                        title = source.get_text(strip=True)
                    
                    # Clean and validate title
                    if title:
                        title = self._sanitize_text(title)
                        # Skip generic titles or site names
                        if (len(title) > 10 and 
                            not title.endswith('...') and
                            not title.lower() in ['nature medicine', 'nature', 'arxiv', 'pubmed', 'ncbi'] and
                            not title.startswith('Error') and
                            not title.startswith('404')):
                            return title
            
        except Exception as e:
            self.logger.warning(f"Failed to extract title from {url}: {str(e)}")
        
        return ""

    def _extract_full_title(self, item: Dict) -> str:
        """Extract full title from Google search result, trying multiple sources."""
        # Try different title sources in order of preference
        title_sources = [
            item.get('title', ''),
            item.get('pagemap', {}).get('metatags', [{}])[0].get('og:title', ''),
            item.get('pagemap', {}).get('metatags', [{}])[0].get('twitter:title', ''),
            item.get('pagemap', {}).get('article', [{}])[0].get('headline', ''),
        ]
        
        for title in title_sources:
            if title and len(title) > 10 and not title.endswith('...') and not title.lower() in ['nature medicine', 'nature', 'arxiv']:
                return self._sanitize_text(title)
        
        # If all titles are truncated, generic, or missing, try scraping the webpage
        link = item.get('link', '')
        if link:
            scraped_title = self._extract_title_from_webpage(link)
            if scraped_title:
                return scraped_title
        
        # Fallback to the first available title, even if truncated
        fallback_title = self._sanitize_text(item.get('title', ''))
        if fallback_title and fallback_title.lower() not in ['nature medicine', 'nature', 'arxiv']:
            return fallback_title
        
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
            
            # Add site-specific searches for RSS feed domains to improve coverage
            rss_domains = [
                "site:aihealth.duke.edu",
                "site:statnews.com", 
                "site:medcitynews.com"
            ]
            
            # Enhance query with RSS domains for better targeting
            enhanced_query = f"{query} ({' OR '.join(rss_domains)})"
            
            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                'key': self.google_api_key,
                'cx': self.google_cx,
                'q': enhanced_query,
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
                
                # Skip if title is too generic or contains job-related keywords
                if any(keyword in title.lower() for keyword in [
                    'job', 'career', 'hiring', 'position', 'vacancy',
                    'employment', 'recruiter', 'hr ', 'human resources'
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
            print("Searching web for Generative AI content...")
            for query in self.SEARCH_QUERIES:
                max_results = self.SOURCE_LIMITS.get('Google Search', default_max)
                entries = self.search_google(query, max_results)
                all_entries.extend(entries)
                total_fetched += len(entries)
                
                # Add small delay to respect API limits
                time.sleep(0.1)
        else:
            print("Google API not configured. Skipping web search.")
        
        # Phase 2: PubMed Search (Academic papers)
        print("Searching PubMed for research papers...")
        pubmed_queries = [
            "generative AI clinical trials",
            "large language model clinical research",
            "synthetic data clinical trials",
            "AI chatbot clinical trials"
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
            "search_queries_used": len(self.SEARCH_QUERIES),
            "search_apis_used": 2  # Google + PubMed
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

                    STRICT CRITERIA - MUST EXPLICITLY MENTION ONE OF THESE IN CLINICAL/HEALTHCARE CONTEXT:
                    
                    TIER 1 - GENERATIVE AI (HIGHEST PRIORITY):
                    - Large Language Models (LLMs): ChatGPT, GPT-4, Claude, Llama, Gemini
                    - Generative AI or "foundation models" for synthetic data generation
                    - AI chatbots or conversational agents for patients/researchers
                    - AI-powered writing tools for protocols, reports, documentation
                    - Natural language generation for clinical content
                    - Synthetic data generation using AI models
                    
                    TIER 2 - APPLIED AI IN CLINICAL RESEARCH (MUST BE SPECIFIC):
                    - Machine learning models for patient recruitment or stratification
                    - Natural language processing for clinical text analysis
                    - Computer vision AI for medical imaging analysis
                    - Predictive AI models for clinical outcomes
                    - AI-powered clinical decision support systems
                    
                    REJECT IMMEDIATELY IF:
                    - Article is about general technology, business news, or career pages
                    - Only mentions "AI" vaguely without specific applications
                    - Discusses basic data analysis or statistics (not AI/ML)
                    - Person profiles or company descriptions without AI research focus
                    - Academic papers on non-AI topics (even if from AI institutions)
                    - General health tech without explicit AI components
                    
                    Article Title: {entry['title']}
                    Article Description: {entry['description'][:500]}
                    
                    CRITICAL ANALYSIS: 
                    1. Does this article EXPLICITLY mention specific AI technologies by name?
                    2. Is there a CLEAR connection to clinical research, clinical trials, or healthcare applications?
                    3. Is this discussing ACTUAL AI implementation, not just general tech or business news?
                    
                    BE STRICT: Only classify as AI-related if you can clearly identify SPECIFIC AI technologies and their DIRECT application in clinical research contexts.

                    You MUST provide ALL FIVE fields:
                    1. is_ai_related: true/false (BE STRICT - only true for explicit AI technology mentions)
                    2. A 50-word summary of the SPECIFIC AI technology mentioned
                    3. A 80-word comment on clinical trial implications
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
                        "comment": "80-word comment on clinical trial implications",
                        "resources": "2-3 resources in bullet format",
                        "ai_tag": "Most specific category from: Generative AI, Machine Learning, Natural Language Processing, Computer Vision, Clinical Decision Support, Trial Optimization, AI Ethics"
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
                                entry['comment'] = self._limit_words(entry['comment'], 100)
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

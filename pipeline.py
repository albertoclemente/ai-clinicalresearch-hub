#!/usr/bin/env python3
"""
Clinical Research Daily Brief Pipeline
Processes RSS feeds, ranks content with OpenAI, generates HTML and PDF output.
"""

import json
import logging
import os
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import re

import feedparser
import openai
from jinja2 import Environment, FileSystemLoader
import weasyprint
import bleach
from dateutil import parser as date_parser
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class FeedProcessor:
    """Handles RSS feed processing and content ranking."""
    
    # RSS feed URLs - expanded with additional clinical research sources
    RSS_FEEDS = [
        # Original 7 feeds
        "https://clinicaltrials.gov/ct2/results/rss.xml",
        "https://www.fda.gov/about-fda/contact-fda/stay-informed/rss-feeds/drug-safety-communications/rss.xml",
        "https://clinicalcenter.nih.gov/rss/news.xml",
        "https://www.nature.com/nm.rss",
        "https://www.nejm.org/action/showFeed?type=etoc&feed=rss",
        "https://www.biopharmadive.com/feeds/news/",
        "https://www.raps.org/news-and-articles/news-articles.rss",
        # Additional clinical research sources
        "https://www.clinicalresearchnewsonline.com/rss",
        "https://endpts.com/channel/news-briefing/feed",
        "https://www.centerwatch.com/rss",
        "https://appliedclinicaltrialsonline.com/rss/full/site",
        "https://www.clinicaltrialsarena.com/feed",
        "https://www.outsourcing-pharma.com/rss",
        "https://acrpnet.org/feed"
    ]
    
    # Source-specific limits for adaptive feed fetching
    SOURCE_LIMITS = {
        'ClinicalTrials.gov': 10,  # High-value official registry
        'FDA': 8,                  # Important regulatory source
        'NIH': 8,                  # Important research source
        'Nature Medicine': 7,      # Top-tier journal
        'NEJM': 7,                 # Top-tier journal
        'Endpoints News': 6,       # Specialized news source
        'BioPharma Dive': 6,       # Industry-focused news
        'Clinical Trials Arena': 6 # Trials-focused news
        # Default for others: 4
    }
    
    def __init__(self, openai_api_key: str, log_file: str):
        """Initialize the feed processor."""
        self.openai_client = openai.OpenAI(api_key=openai_api_key)
        self.logger = self._setup_logging(log_file)
        self.brief_date = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        
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
    
    def fetch_feeds(self, default_max: int = 4) -> List[Dict]:
        """Fetch and parse all RSS feeds, with adaptive limits per source and filtering recent articles."""
        all_entries = []
        total_fetched = 0
        
        # Only consider articles from the last 7 days
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=7)
        
        for feed_url in self.RSS_FEEDS:
            timestamp = datetime.now(timezone.utc).isoformat()
            source_name = self._get_source_name(feed_url)
            
            # Get source-specific limit or use default
            max_entries = self.SOURCE_LIMITS.get(source_name, default_max)
            
            try:
                feed = feedparser.parse(feed_url)
                
                # Log successful request
                status = getattr(feed, 'status', 200)
                self._log_feed_request(feed_url, status, timestamp)
                
                # Limit entries per feed and sort by publication date (newest first)
                entries = feed.entries[:max_entries * 2]  # Get extra to sort properly
                
                # Sort by publication date (newest first) and take only the latest ones
                sorted_entries = sorted(entries, 
                                      key=lambda x: self._parse_date(x.get('published', '')), 
                                      reverse=True)[:max_entries]
                
                source_fetched = 0
                
                for entry in sorted_entries:
                    # Parse publication date
                    pub_date = self._parse_date(entry.get('published', ''))
                    pub_datetime = datetime.fromisoformat(pub_date.replace('Z', '+00:00'))
                    
                    # Skip articles older than 7 days
                    if pub_datetime < cutoff_date:
                        continue
                    
                    # Extract and sanitize entry data
                    entry_data = {
                        'id': str(uuid.uuid4()),
                        'title': self._sanitize_text(entry.get('title', '')),
                        'description': self._sanitize_text(entry.get('description', '')),
                        'link': entry.get('link', ''),
                        'pub_date': pub_date,
                        'source': source_name,
                        'brief_date': self.brief_date
                    }
                    
                    if entry_data['title'] and entry_data['link']:
                        all_entries.append(entry_data)
                        source_fetched += 1
                
                # Log how many articles were fetched from this source
                self.logger.info(json.dumps({
                    "timestamp": timestamp,
                    "source": source_name,
                    "articles_fetched": source_fetched,
                    "max_allowed": max_entries
                }))
                
                total_fetched += source_fetched
                        
            except Exception as e:
                self._log_feed_request(feed_url, 0, timestamp, str(e))
                continue
        
        self.logger.info(json.dumps({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_articles_fetched": total_fetched,
            "sources_processed": len(self.RSS_FEEDS)
        }))
                
        return all_entries
    
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
            'clinicaltrials.gov': 'ClinicalTrials.gov',
            'fda.gov': 'FDA',
            'nih.gov': 'NIH',
            'nature.com': 'Nature Medicine',
            'nejm.org': 'NEJM',
            'biopharmadive.com': 'BioPharma Dive',
            'raps.org': 'RAPS',
            'clinicalresearchnewsonline.com': 'Clinical Research News',
            'endpts.com': 'Endpoints News',
            'centerwatch.com': 'CenterWatch Weekly',
            'appliedclinicaltrialsonline.com': 'Applied Clinical Trials',
            'clinicaltrialsarena.com': 'Clinical Trials Arena',
            'outsourcing-pharma.com': 'Outsourcing-Pharma',
            'acrpnet.org': 'ACRP Blog'
        }
        
        for domain, name in source_mapping.items():
            if domain in feed_url:
                return name
        
        return 'Unknown'
    
    def score_with_llm(self, entries: List[Dict]) -> List[Dict]:
        """Score entries using OpenAI API with temperature 0.3."""
        scored_entries = []
        
        for entry in entries:
            # Try up to 3 times to ensure we get all required fields
            for attempt in range(3):
                try:
                    prompt = f"""
                    You are a clinical research expert. You MUST provide ALL THREE of the following for this article:
                    1. A relevance score (0-5, where 5 is most relevant to clinical research professionals)
                    2. A 60-word summary focusing on key clinical research insights
                    3. A 70-word insightful comment that stimulates deeper thinking by:
                       - Connecting the news to broader industry trends or challenges
                       - Posing thought-provoking questions that highlight implications
                       - Identifying tensions or contradictions worth exploring
                       - Suggesting new perspectives or angles that aren't immediately obvious
                       - Sparking the reader's curiosity to learn more about the subject
                    
                    Article Title: {entry['title']}
                    Article Description: {entry['description'][:500]}
                    
                    IMPORTANT INSTRUCTIONS FOR COMMENT:
                    - Your comment MUST be complete, not cut off mid-thought
                    - Express complete ideas in 70 words or less
                    - Avoid trailing fragments that would be cut off
                    - Don't end with "..." or incomplete sentences
                    
                    You MUST respond in this exact JSON format with ALL THREE fields:
                    {{
                        "score": 0.0,
                        "summary": "Your 60-word summary here",
                        "comment": "Your complete 70-word insightful comment here"
                    }}
                    
                    IMPORTANT: All three fields (score, summary, comment) are REQUIRED. Do not omit any field.
                    """
                    
                    response = self.openai_client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.3,
                        max_tokens=400
                    )
                    
                    # Parse the JSON response
                    content = response.choices[0].message.content.strip()
                    
                    # Extract JSON from response
                    json_match = re.search(r'\{.*\}', content, re.DOTALL)
                    if json_match:
                        result = json.loads(json_match.group())
                        
                        # Validate all required fields are present and valid
                        if self._validate_llm_response(result):
                            entry['score'] = float(result.get('score', 0))
                            entry['summary'] = self._sanitize_text(result.get('summary', ''))
                            entry['comment'] = self._sanitize_text(result.get('comment', ''))
                            
                            # Ensure word limits
                            entry['summary'] = self._limit_words(entry['summary'], 60)
                            entry['comment'] = self._limit_words(entry['comment'], 70)
                            
                            scored_entries.append(entry)
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
                    self.logger.error(f"Error scoring entry {entry['id']}, attempt {attempt + 1}: {str(e)}")
                    if attempt == 2:  # Last attempt
                        continue
        
        return scored_entries
    
    def _validate_llm_response(self, result: Dict) -> bool:
        """Validate that LLM response contains all required fields with valid content."""
        required_fields = ['score', 'summary', 'comment']
        
        for field in required_fields:
            if field not in result:
                return False
            
            value = result[field]
            
            # Validate score
            if field == 'score':
                try:
                    score = float(value)
                    if not (0 <= score <= 5):
                        return False
                except (ValueError, TypeError):
                    return False
            
            # Validate summary and comment
            elif field in ['summary', 'comment']:
                if not isinstance(value, str) or len(value.strip()) < 10:
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
    
    def select_top_items(self, entries: List[Dict]) -> List[Dict]:
        """Select top 8-10 items with score >= 3, tie-break by pub_date."""
        # Filter by minimum score
        filtered = [entry for entry in entries if entry.get('score', 0) >= 3.0]
        
        # Sort by score (descending) then by pub_date (descending)
        sorted_entries = sorted(
            filtered,
            key=lambda x: (x.get('score', 0), x.get('pub_date', '')),
            reverse=True
        )
        
        # Return top 8-10 items
        return sorted_entries[:10]
    
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
    """Handles HTML and PDF generation using Jinja2 and WeasyPrint."""
    
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
    
    def generate_pdf(self, brief_data: Dict, output_file: str):
        """Generate PDF using WeasyPrint."""
        template = self.env.get_template('pdf.html')
        
        # Prepare template context
        context = {
            'brief_date': brief_data['brief_date'],
            'generated_at': brief_data['generated_at'],
            'items': brief_data['items'],
            'total_items': brief_data['total_items']
        }
        
        # Render template
        html_content = template.render(**context)
        
        # Generate PDF
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        weasyprint.HTML(string=html_content).write_pdf(output_file)


def main():
    """Main pipeline execution."""
    # Configuration
    openai_api_key = os.environ.get('OPENAI_API_KEY')
    if not openai_api_key:
        raise ValueError("OPENAI_API_KEY environment variable is required")
    
    # Configuration: Default max entries for sources without specific limits
    default_max_entries = int(os.environ.get('DEFAULT_MAX_ENTRIES', '4'))
    
    brief_date = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    log_file = f"logs/{brief_date}.log"
    json_file = f"briefs/{brief_date}.json"
    html_file = "site/index.html"
    pdf_file = f"briefs/{brief_date}.pdf"
    
    # Initialize processors
    feed_processor = FeedProcessor(openai_api_key, log_file)
    site_generator = SiteGenerator()
    
    print(f"Starting Clinical Research Daily Brief pipeline for {brief_date}")
    
    # Step 1: Fetch feeds with adaptive limits per source
    print("Fetching RSS feeds with adaptive source limits...")
    entries = feed_processor.fetch_feeds(default_max=default_max_entries)
    print(f"Fetched {len(entries)} entries from {len(feed_processor.RSS_FEEDS)} RSS feeds (with adaptive source limits)")
    
    # Step 2: Score with LLM
    print("Scoring entries with OpenAI...")
    scored_entries = feed_processor.score_with_llm(entries)
    print(f"Scored {len(scored_entries)} entries")
    
    # Step 3: Select top items
    print("Selecting top items...")
    top_items = feed_processor.select_top_items(scored_entries)
    print(f"Selected {len(top_items)} top items")
    
    # Step 4: Save brief data
    print("Saving brief data...")
    feed_processor.save_brief_data(top_items, json_file)
    
    # Step 5: Generate HTML
    print("Generating HTML...")
    with open(json_file, 'r', encoding='utf-8') as f:
        brief_data = json.load(f)
    site_generator.generate_html(brief_data, html_file)
    
    # Step 6: Generate PDF
    print("Generating PDF...")
    site_generator.generate_pdf(brief_data, pdf_file)
    
    print(f"Pipeline completed successfully!")
    print(f"- Brief data: {json_file}")
    print(f"- HTML page: {html_file}")
    print(f"- PDF archive: {pdf_file}")
    print(f"- Logs: {log_file}")


if __name__ == "__main__":
    main()

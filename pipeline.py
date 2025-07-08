#!/usr/bin/env python3
"""
AI in Clinical Research Bi-Weekly Brief Pipeline
Processes RSS feeds, identifies AI-related content, generates HTML and PDF output.
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
# import weasyprint  # Temporarily disabled due to dependency issues
import bleach
from dateutil import parser as date_parser
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class FeedProcessor:
    """Handles RSS feed processing and AI content identification."""
    
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
    
    # Source-specific limits for AI content discovery - increased for better coverage
    SOURCE_LIMITS = {
        'ClinicalTrials.gov': 15,      # Increased for more trial data
        'FDA': 12,                     # Increased for regulatory AI news
        'NIH': 12,                     # Increased for research insights
        'Nature Medicine': 10,         # Increased for academic papers
        'NEJM': 10,                   # Increased for clinical studies
        'BioPharma Dive': 8,          # Industry AI news
        'Endpoints News': 8,          # Biotech AI developments
        'Clinical Trials Arena': 8,   # Trial technology news
        'RAPS': 6,                    # Regulatory perspective
        'Clinical Research News': 6,  # Research updates
        'CenterWatch Weekly': 6,      # Trial management
        'Applied Clinical Trials': 6, # Methodology advances
        'Outsourcing-Pharma': 6,     # Industry trends
        'ACRP Blog': 6               # Professional insights
        # Default for others: 5
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
        
        # Only consider articles from the last 30 days (bi-weekly with broader coverage)
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=30)
        
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
                    
                    # Skip articles older than 30 days
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
    
    def identify_ai_content(self, entries: List[Dict]) -> List[Dict]:
        """Identify AI-related articles and tag them using OpenAI API."""
        ai_entries = []
        
        for entry in entries:
            # Try up to 3 times to ensure we get all required fields
            for attempt in range(3):
                try:
                    prompt = f"""
                    You are an AI and clinical research expert. Analyze this article to determine if it relates to AI in clinical research.

                    AI in clinical research includes:
                    - Machine learning in drug discovery/development
                    - AI for patient recruitment and trial optimization
                    - Natural language processing for clinical data
                    - Computer vision for medical imaging in trials
                    - Predictive analytics for clinical outcomes
                    - Digital biomarkers and wearable technology
                    - AI-powered diagnostic tools in clinical settings
                    - Robotic process automation in clinical operations
                    - Large language models for clinical decision support
                    - AI for regulatory submissions and compliance
                    - Digital therapeutics and AI-based interventions
                    - Real-world evidence collection using AI
                    - AI ethics in clinical research
                    - Computational biology and bioinformatics
                    
                    Article Title: {entry['title']}
                    Article Description: {entry['description'][:500]}
                    
                    You MUST provide ALL FIVE of the following:
                    1. is_ai_related: true/false - Does this discuss AI/ML/advanced computational methods in clinical research?
                    2. A 60-word summary focusing on AI applications in clinical research
                    3. A 100-word insightful comment about implications, challenges, opportunities, or future directions
                    4. A 60-word resources section suggesting specific websites, tools, databases, or further reading
                    5. ai_tag: One specific category from the list below
                    
                    AI Tags (choose the most appropriate one):
                    - "Machine Learning"
                    - "Natural Language Processing" 
                    - "Computer Vision"
                    - "Predictive Analytics"
                    - "Digital Biomarkers"
                    - "AI Diagnostics"
                    - "Clinical Decision Support"
                    - "Drug Discovery AI"
                    - "Trial Optimization"
                    - "Regulatory AI"
                    - "Digital Therapeutics"
                    - "AI Ethics"
                    
                    ENHANCED INSTRUCTIONS FOR HIGH-QUALITY OUTPUT:
                    
                    For the COMMENT field (100 words), be deeply insightful by:
                    - Analyzing the BROADER IMPLICATIONS: What does this mean for the future of clinical research?
                    - Identifying KEY CHALLENGES: What obstacles need to be overcome?
                    - Highlighting OPPORTUNITIES: What new possibilities does this create?
                    - Discussing STAKEHOLDER IMPACT: How does this affect patients, researchers, regulators?
                    - Connecting to EMERGING TRENDS: How does this fit into the larger AI revolution in healthcare?
                    - Raising THOUGHT-PROVOKING QUESTIONS: What should researchers be considering?
                    
                    For the RESOURCES field (60 words), provide ARTICLE-SPECIFIC and ACTIONABLE suggestions:
                    - Suggest RELATED PAPERS: "PubMed: '[specific search terms from this article]'" or "Similar studies: [specific keywords]"
                    - Cite RELEVANT TOOLS/PLATFORMS: Based on the specific AI method mentioned (e.g., if NLP mentioned: "spaCy clinical models", if ML: "scikit-learn medical datasets")
                    - Reference SPECIFIC DATASETS: Related to the disease/condition/method discussed
                    - Suggest TARGETED SEARCHES: "Google Scholar: '[author name] + [specific technique]'" or "ClinicalTrials.gov: '[specific condition] + AI'"
                    - Include RELATED ORGANIZATIONS: Specific to the research area (e.g., if cancer AI: "NCI AI initiatives", if rare diseases: "NORD AI programs")
                    - Recommend FOCUSED LEARNING: Courses/resources specific to the AI technique or medical area discussed
                    
                    CRITICAL: Resources must be DIRECTLY RELATED to this specific article's content, not generic AI resources.
                    
                    You MUST respond in this exact JSON format:
                    {{
                        "is_ai_related": true/false,
                        "summary": "Your 60-word summary focusing on AI aspects",
                        "comment": "Your 100-word deeply insightful comment about AI implications, challenges, and opportunities",
                        "resources": "Your 60-word article-specific resources with targeted searches, related papers, and relevant tools/datasets",
                        "ai_tag": "One of the specific tags from the list above"
                    }}
                    
                    CRITICAL: All five fields are REQUIRED. Resources must be DIRECTLY RELATED to this specific article's content, authors, methods, or medical area.
                    """
                    
                    response = self.openai_client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.3,
                        max_tokens=500
                    )
                    
                    # Parse the JSON response
                    content = response.choices[0].message.content.strip()
                    
                    # Extract JSON from response
                    json_match = re.search(r'\{.*\}', content, re.DOTALL)
                    if json_match:
                        result = json.loads(json_match.group())
                        
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
                                entry['resources'] = self._limit_words(entry['resources'], 60)
                                
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
            
            # Validate text fields
            elif field in ['summary', 'comment', 'resources', 'ai_tag']:
                if not isinstance(value, str) or len(value.strip()) < 5:
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
        """Select and sort AI-related articles by publication date."""
        # Sort by publication date (descending) to show newest first
        sorted_entries = sorted(
            entries,
            key=lambda x: x.get('pub_date', ''),
            reverse=True
        )
        
        # Return all AI-related articles (already filtered in identify_ai_content)
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
        # weasyprint.HTML(string=html_content).write_pdf(output_file)  # Temporarily disabled
        print(f"PDF generation temporarily disabled due to dependency issues")


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
    
    print(f"Starting AI in Clinical Research Bi-Weekly Brief pipeline for {brief_date}")
    
    # Step 1: Fetch feeds with adaptive limits per source
    print("Fetching RSS feeds with adaptive source limits...")
    entries = feed_processor.fetch_feeds(default_max=default_max_entries)
    print(f"Fetched {len(entries)} entries from {len(feed_processor.RSS_FEEDS)} RSS feeds (with adaptive source limits)")
    
    # Step 2: Identify AI-related content
    print("Identifying AI-related articles with OpenAI...")
    ai_entries = feed_processor.identify_ai_content(entries)
    print(f"Identified {len(ai_entries)} AI-related articles")
    
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
    
    # Step 6: Generate PDF
    print("Generating PDF...")
    # site_generator.generate_pdf(brief_data, pdf_file)  # Temporarily disabled
    print("PDF generation temporarily disabled due to dependency issues")
    
    print(f"Pipeline completed successfully!")
    print(f"- Brief data: {json_file}")
    print(f"- HTML page: {html_file}")
    print(f"- PDF archive: {pdf_file}")
    print(f"- Logs: {log_file}")


if __name__ == "__main__":
    main()

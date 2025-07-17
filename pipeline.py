#!/usr/bin/env python3
"""
AI in Clinical Research Brief Pipeline
Processes RSS feeds, identifies AI-specific content in clinical research, generates HTML and PDF output.
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
    """Handles RSS feed processing and AI content identification in clinical research."""
    
    # RSS feed URLs - focused on AI applications in clinical research and trials
    RSS_FEEDS = [
        # AI and Healthcare Research (High Priority)
        "https://www.nature.com/subjects/machine-learning.rss",  # Nature Machine Learning
        "https://www.nature.com/subjects/artificial-intelligence.rss",  # Nature AI
        "https://www.nature.com/ndigital.rss",  # Nature Digital Medicine
        "https://www.nature.com/subjects/medical-research.rss",  # Nature Medical Research
        "https://www.nature.com/npjdigitalmed.rss",  # NPJ Digital Medicine
        # Generative AI and Clinical Focus
        "https://www.statnews.com/tag/artificial-intelligence/feed/",  # STAT AI Coverage
        "https://www.statnews.com/tag/generative-ai/feed/",  # STAT Generative AI
        "https://www.mobihealthnews.com/feeds/news",  # Digital Health & AI News
        "https://venturebeat.com/ai/feed/",  # VentureBeat AI (includes healthcare AI)
        "https://www.healthcareitnews.com/rss.xml",  # Healthcare IT News (AI applications)
        "https://www.healthcarefinancenews.com/rss.xml",  # Healthcare Finance News (AI investments)
        # Academic and Research Sources (Expanded)
        "https://arxiv.org/rss/cs.AI",  # arXiv AI (includes biomedical AI)
        "https://arxiv.org/rss/cs.LG",  # arXiv Machine Learning
        "https://arxiv.org/rss/cs.CL",  # arXiv Computational Linguistics (LLMs)
        "https://arxiv.org/rss/cs.HC",  # arXiv Human-Computer Interaction (clinical AI)
        "https://arxiv.org/rss/q-bio.QM",  # arXiv Quantitative Biology
        "https://connect.medrxiv.org/relate/content/181",  # medRxiv AI/ML papers
        # AI in Drug Discovery and Clinical Trials
        "https://www.drugdiscoverytoday.com/rss",  # Drug Discovery Today (AI focus)
        "https://www.clinicaltrialsarena.com/rss",  # Clinical Trials Arena
        "https://www.appliedclinicaltrialsonline.com/rss",  # Applied Clinical Trials
        # Industry and Clinical AI (Enhanced)
        "https://www.fiercehealthcare.com/rss",  # Fierce Healthcare (includes AI)
        "https://www.modernhealthcare.com/rss",  # Modern Healthcare
        "https://www.healthleadersmedia.com/rss",  # Health Leaders (AI in healthcare)
        "https://www.beckersspine.com/rss",  # Becker's Healthcare (AI coverage)
        # AI and Regulatory
        "https://www.fda.gov/about-fda/contact-fda/fda-rss-feeds",  # FDA RSS (regulatory AI)
        "https://www.raps.org/RSS",  # RAPS Regulatory Affairs (AI regulatory)
        # Specialized AI/ML Healthcare Sources
        "https://hai.stanford.edu/news/rss.xml",  # Stanford HAI (Human-Centered AI)
        "https://www.microsoft.com/en-us/research/feed/",  # Microsoft Research (healthcare AI)
        # General clinical sources (backup)
        "https://endpts.com/feed/",  # Endpoints News
        "https://www.biopharmadive.com/feeds/news",  # BioPharma Dive
    ]
    
    # Source-specific limits for AI in clinical research content discovery
    SOURCE_LIMITS = {
        # AI and Healthcare Research (High Priority)
        'Nature ML': 15,                # Nature Machine Learning
        'Nature AI': 15,                # Nature AI
        'Nature Digital Medicine': 12,  # Nature Digital Medicine
        'Nature Medical Research': 10,  # Nature Medical Research
        'NPJ Digital Medicine': 12,     # NPJ Digital Medicine
        # Generative AI and Clinical Focus
        'STAT AI': 15,                  # STAT AI Coverage
        'STAT Generative AI': 12,       # STAT Generative AI
        'MobiHealthNews': 12,           # Digital Health & AI News
        'VentureBeat AI': 10,           # VentureBeat AI
        'Healthcare IT News': 12,       # Healthcare IT News
        'Healthcare Finance News': 8,   # Healthcare Finance News
        # Academic and Research (Expanded)
        'arXiv AI': 12,                 # AI preprints
        'arXiv ML': 12,                 # ML preprints
        'arXiv CL': 10,                 # Computational Linguistics (LLMs)
        'arXiv HC': 8,                  # Human-Computer Interaction
        'arXiv Bio': 10,                # Computational biology
        'medRxiv': 15,                  # Medical AI preprints
        # AI in Drug Discovery and Clinical Trials
        'Drug Discovery Today': 10,     # Drug discovery AI
        'Clinical Trials Arena': 12,    # Clinical trials
        'Applied Clinical Trials': 10,  # Applied clinical trials
        # Industry and Clinical AI (Enhanced)
        'Fierce Healthcare': 12,        # Healthcare industry
        'Modern Healthcare': 10,        # Healthcare news
        'Health Leaders': 10,           # Healthcare leadership
        'Beckers Healthcare': 8,        # Healthcare technology
        # AI and Regulatory
        'FDA RSS': 8,                   # FDA regulatory
        'RAPS Regulatory': 8,           # Regulatory affairs
        # Specialized AI/ML Healthcare
        'Stanford HAI': 10,             # Human-centered AI
        'Microsoft Research': 8,        # Microsoft healthcare AI
        # Backup sources
        'Endpoints News': 10,           # Industry coverage
        'BioPharma Dive': 10,           # Biotech/pharma news
        # Default for others: 8
    }
    
    def __init__(self, openai_api_key: str, log_file: str, days_back: int = 60):
        """Initialize the feed processor.
        
        Args:
            openai_api_key: OpenAI API key for content analysis
            log_file: Path to log file
            days_back: Number of days back to consider articles (default: 60)
        """
        self.openai_client = openai.OpenAI(api_key=openai_api_key)
        self.logger = self._setup_logging(log_file)
        self.brief_date = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        self.days_back = days_back
        
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
    
    def fetch_feeds(self, default_max: int = 8) -> List[Dict]:
        """Fetch and parse all RSS feeds, with adaptive limits per source and filtering recent articles."""
        all_entries = []
        total_fetched = 0
        
        # Use configurable timeframe instead of fixed 30 days
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=self.days_back)
        
        self.logger.info(json.dumps({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "days_back": self.days_back,
            "cutoff_date": cutoff_date.isoformat(),
            "message": f"Fetching articles from the last {self.days_back} days"
        }))
        
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
                    
                    # Skip articles older than the configured timeframe
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
            # AI and Healthcare Research (High Priority)
            'nature.com/subjects/machine-learning': 'Nature ML',
            'nature.com/subjects/artificial-intelligence': 'Nature AI',
            'nature.com/ndigital': 'Nature Digital Medicine',
            'nature.com/subjects/medical-research': 'Nature Medical Research',
            'nature.com/npjdigitalmed': 'NPJ Digital Medicine',
            # Generative AI and Clinical Focus
            'statnews.com/tag/artificial-intelligence': 'STAT AI',
            'statnews.com/tag/generative-ai': 'STAT Generative AI',
            'mobihealthnews.com': 'MobiHealthNews',
            'venturebeat.com/ai': 'VentureBeat AI',
            'healthcareitnews.com': 'Healthcare IT News',
            'healthcarefinancenews.com': 'Healthcare Finance News',
            # Academic and Research (Expanded)
            'arxiv.org/rss/cs.AI': 'arXiv AI',
            'arxiv.org/rss/cs.LG': 'arXiv ML',
            'arxiv.org/rss/cs.CL': 'arXiv CL',
            'arxiv.org/rss/cs.HC': 'arXiv HC',
            'arxiv.org/rss/q-bio.QM': 'arXiv Bio',
            'connect.medrxiv.org': 'medRxiv',
            # AI in Drug Discovery and Clinical Trials
            'drugdiscoverytoday.com': 'Drug Discovery Today',
            'clinicaltrialsarena.com': 'Clinical Trials Arena',
            'appliedclinicaltrialsonline.com': 'Applied Clinical Trials',
            # Industry and Clinical AI (Enhanced)
            'fiercehealthcare.com': 'Fierce Healthcare',
            'modernhealthcare.com': 'Modern Healthcare',
            'healthleadersmedia.com': 'Health Leaders',
            'beckersspine.com': 'Beckers Healthcare',
            # AI and Regulatory
            'fda.gov': 'FDA RSS',
            'raps.org': 'RAPS Regulatory',
            # Specialized AI/ML Healthcare
            'hai.stanford.edu': 'Stanford HAI',
            'microsoft.com/en-us/research': 'Microsoft Research',
            # Backup sources
            'endpts.com': 'Endpoints News',
            'biopharmadive.com': 'BioPharma Dive'
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
                    You are an AI and clinical research expert. Analyze this article to determine if it SPECIFICALLY relates to AI, Machine Learning, or Generative AI being used in clinical research or clinical trials contexts.

                    PRIORITIZE GENERATIVE AI applications and ONLY classify as AI-related if the article explicitly discusses:
                    
                    GENERATIVE AI IN CLINICAL RESEARCH (HIGH PRIORITY):
                    - Large Language Models (LLMs) for clinical decision support, documentation, or patient communication
                    - Generative AI for synthetic clinical data generation
                    - AI-powered chatbots for patient engagement in clinical trials
                    - Generative models for drug design and molecular discovery
                    - LLMs for clinical protocol writing and trial design
                    - Generative AI for medical image synthesis in clinical studies
                    - Foundation models adapted for healthcare and clinical applications
                    - AI assistants for clinical researchers and trial coordinators
                    
                    OTHER AI/ML IN CLINICAL RESEARCH:
                    - Machine learning algorithms in drug discovery/development
                    - AI systems for patient recruitment and trial optimization
                    - Natural language processing for clinical data analysis
                    - Computer vision for medical imaging in clinical trials
                    - Predictive analytics for clinical outcomes
                    - Digital biomarkers using AI/ML technology
                    - AI-powered diagnostic tools in clinical settings
                    - Real-world evidence collection using AI/ML
                    - AI ethics specifically in clinical research contexts
                    - Computational biology and bioinformatics with AI/ML methods

                    EXCLUDE articles that only discuss:
                    - General AI research without clinical applications
                    - Traditional clinical trial results without AI/ML components
                    - Standard medical devices or procedures
                    - General healthcare policy without AI focus
                    - Basic digital health tools without AI/ML
                    - Traditional statistical analysis or research methods
                    
                    Article Title: {entry['title']}
                    Article Description: {entry['description'][:500]}
                    
                    CRITICAL: Only set is_ai_related to true if the article explicitly mentions AI, machine learning, artificial intelligence, neural networks, deep learning, NLP, computer vision, LLMs, generative AI, or other advanced computational methods SPECIFICALLY in clinical research or clinical trials contexts.
                    
                    You MUST provide ALL FIVE of the following:
                    1. is_ai_related: true/false - Does this EXPLICITLY discuss AI/ML/Generative AI/advanced computational methods in clinical research?
                    2. A 60-word summary focusing on the specific AI/ML applications in clinical research
                    3. A 100-word insightful comment about AI implications, challenges, opportunities, or future directions
                    4. A 60-word resources section suggesting AI-specific websites, tools, datasets, or further reading
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
                    - "Generative AI"
                    
                    ENHANCED INSTRUCTIONS FOR HIGH-QUALITY OUTPUT:
                    
                    For the COMMENT field (100 words), be deeply insightful by:
                    - Analyzing the BROADER IMPLICATIONS: What does this mean for the future of clinical research?
                    - Identifying KEY CHALLENGES: What obstacles need to be overcome?
                    - Highlighting OPPORTUNITIES: What new possibilities does this create?
                    - Discussing STAKEHOLDER IMPACT: How does this affect patients, researchers, regulators?
                    - Connecting to EMERGING TRENDS: How does this fit into the larger AI revolution in healthcare?
                    - Raising THOUGHT-PROVOKING QUESTIONS: What should researchers be considering?
                    
                    For the RESOURCES field, provide 2-3 ARTICLE-SPECIFIC resources in this EXACT format:
                    • [Brief description]: [Actual URL or specific search instruction]
                    • [Brief description]: [Actual URL or specific search instruction]
                    • [Brief description]: [Actual URL or specific search instruction]
                    
                    Resource types to include:
                    - RELATED RESEARCH: "PubMed search for '[specific terms]': https://pubmed.ncbi.nlm.nih.gov/?term=[encoded_terms]"
                    - RELEVANT TOOLS: "Tool name for [specific use]": https://actual-tool-url.com"
                    - DATASETS: "Dataset for [specific purpose]": https://dataset-url.com"
                    - ORGANIZATIONS: "Organization working on [specific area]": https://org-website.com"
                    - LEARNING RESOURCES: "Course on [specific topic]": https://course-url.com"
                    
                    Example format:
                    • Related research on LLM clinical applications: https://pubmed.ncbi.nlm.nih.gov/?term=LLM+clinical+decision+support
                    • Hugging Face medical transformers: https://huggingface.co/models?pipeline_tag=text-classification&domain=medical
                    • NIH Bridge2AI initiative: https://bridge2ai.nih.gov/
                    
                    CRITICAL: Provide REAL, working URLs when possible. For searches, use actual search URLs with encoded terms.
                    
                    You MUST respond in this exact JSON format:
                    {{
                        "is_ai_related": true/false,
                        "summary": "Your 60-word summary focusing on AI aspects",
                        "comment": "Your 100-word deeply insightful comment about AI implications, challenges, and opportunities",
                        "resources": "2-3 resources in bullet format with descriptions and links as specified above",
                        "ai_tag": "One of the specific tags from the list above"
                    }}
                    
                    CRITICAL: All five fields are REQUIRED. Resources must include brief descriptions and actual URLs/links when possible.
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
        print(f"PDF generated successfully: {output_file}")


def main():
    """Main pipeline execution."""
    # Configuration
    openai_api_key = os.environ.get('OPENAI_API_KEY')
    if not openai_api_key:
        raise ValueError("OPENAI_API_KEY environment variable is required")
    
    # Configuration: Default max entries for sources without specific limits
    default_max_entries = int(os.environ.get('DEFAULT_MAX_ENTRIES', '8'))
    
    # Configuration: Timeframe for article collection (configurable via environment)
    days_back = int(os.environ.get('DAYS_BACK', '60'))  # Default to 60 days
    
    brief_date = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    log_file = f"logs/{brief_date}.log"
    json_file = f"briefs/{brief_date}.json"
    html_file = "site/index.html"
    pdf_file = f"briefs/{brief_date}.pdf"
    
    # Initialize processors
    feed_processor = FeedProcessor(openai_api_key, log_file, days_back)
    site_generator = SiteGenerator()
    
    print(f"Starting AI in Clinical Research Brief pipeline for {brief_date}")
    print(f"Collecting articles from the last {days_back} days")
    
    # Step 1: Fetch feeds with adaptive limits per source
    print("Fetching RSS feeds with adaptive source limits...")
    entries = feed_processor.fetch_feeds(default_max=default_max_entries)
    print(f"Fetched {len(entries)} entries from {len(feed_processor.RSS_FEEDS)} RSS feeds (with adaptive source limits)")
    
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

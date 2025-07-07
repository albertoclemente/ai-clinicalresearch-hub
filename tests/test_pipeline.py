"""
Tests for Clinical Research Daily Brief Pipeline
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest
import feedparser

from pipeline import FeedProcessor, SiteGenerator


class TestFeedProcessor:
    """Test the FeedProcessor class."""
    
    def test_init(self, temp_dir, mock_openai_api_key):
        """Test FeedProcessor initialization."""
        log_file = os.path.join(temp_dir, "test.log")
        processor = FeedProcessor(mock_openai_api_key, log_file)
        
        assert processor.openai_client is not None
        assert processor.logger is not None
        assert processor.brief_date is not None
        assert Path(log_file).exists()
    
    def test_sanitize_text(self, temp_dir, mock_openai_api_key):
        """Test text sanitization."""
        log_file = os.path.join(temp_dir, "test.log")
        processor = FeedProcessor(mock_openai_api_key, log_file)
        
        # Test HTML removal
        dirty_text = "<script>alert('xss')</script>Test content"
        clean_text = processor._sanitize_text(dirty_text)
        assert "<script>" not in clean_text
        assert "Test content" in clean_text
        
        # Test whitespace normalization
        whitespace_text = "  Multiple   spaces  \n\t  "
        clean_text = processor._sanitize_text(whitespace_text)
        assert clean_text == "Multiple spaces"
    
    def test_get_source_name(self, temp_dir, mock_openai_api_key):
        """Test source name extraction."""
        log_file = os.path.join(temp_dir, "test.log")
        processor = FeedProcessor(mock_openai_api_key, log_file)
        
        test_cases = [
            ("https://clinicaltrials.gov/rss.xml", "ClinicalTrials.gov"),
            ("https://www.fda.gov/feed.xml", "FDA"),
            ("https://clinicalcenter.nih.gov/feed.xml", "NIH"),
            ("https://www.nature.com/feed.xml", "Nature Medicine"),
            ("https://www.nejm.org/feed.xml", "NEJM"),
            ("https://www.biopharmadive.com/feed.xml", "BioPharma Dive"),
            ("https://www.raps.org/feed.xml", "RAPS"),
            ("https://unknown.com/feed.xml", "Unknown")
        ]
        
        for url, expected_name in test_cases:
            assert processor._get_source_name(url) == expected_name
    
    def test_limit_words(self, temp_dir, mock_openai_api_key):
        """Test word limiting functionality."""
        log_file = os.path.join(temp_dir, "test.log")
        processor = FeedProcessor(mock_openai_api_key, log_file)
        
        # Test within limit
        short_text = "This is a short text"
        result = processor._limit_words(short_text, 10)
        assert result == short_text
        
        # Test exceeding limit
        long_text = "This is a very long text that exceeds the word limit"
        result = processor._limit_words(long_text, 5)
        assert result == "This is a very long..."
        assert len(result.split()) <= 6  # 5 words + "..."
    
    def test_select_top_items(self, temp_dir, mock_openai_api_key):
        """Test top items selection."""
        log_file = os.path.join(temp_dir, "test.log")
        processor = FeedProcessor(mock_openai_api_key, log_file)
        
        # Create test entries with different scores
        entries = [
            {'score': 2.5, 'pub_date': '2025-01-01T00:00:00Z', 'title': 'Low score'},
            {'score': 4.0, 'pub_date': '2025-01-02T00:00:00Z', 'title': 'High score 1'},
            {'score': 3.5, 'pub_date': '2025-01-03T00:00:00Z', 'title': 'Medium score'},
            {'score': 4.0, 'pub_date': '2025-01-01T00:00:00Z', 'title': 'High score 2'},
            {'score': 5.0, 'pub_date': '2025-01-04T00:00:00Z', 'title': 'Top score'},
        ]
        
        top_items = processor.select_top_items(entries)
        
        # Should filter out score < 3.0
        assert len(top_items) == 4
        assert all(item['score'] >= 3.0 for item in top_items)
        
        # Should be sorted by score (descending)
        assert top_items[0]['score'] == 5.0
        assert top_items[0]['title'] == 'Top score'
        
        # Test tie-breaking by pub_date
        high_score_items = [item for item in top_items if item['score'] == 4.0]
        assert len(high_score_items) == 2
        # More recent date should come first
        assert high_score_items[0]['pub_date'] > high_score_items[1]['pub_date']
    
    def test_save_brief_data(self, temp_dir, mock_openai_api_key):
        """Test saving brief data to JSON."""
        log_file = os.path.join(temp_dir, "test.log")
        output_file = os.path.join(temp_dir, "brief.json")
        processor = FeedProcessor(mock_openai_api_key, log_file)
        
        test_entries = [
            {
                'id': 'test-1',
                'title': 'Test Article',
                'score': 4.5,
                'summary': 'Test summary',
                'comment': 'Test comment'
            }
        ]
        
        processor.save_brief_data(test_entries, output_file)
        
        # Check file was created
        assert Path(output_file).exists()
        
        # Check content
        with open(output_file, 'r') as f:
            data = json.load(f)
        
        assert data['brief_date'] == processor.brief_date
        assert data['total_items'] == 1
        assert len(data['items']) == 1
        assert data['items'][0]['title'] == 'Test Article'
    
    @patch('feedparser.parse')
    def test_fetch_feeds_success(self, mock_parse, temp_dir, mock_openai_api_key):
        """Test successful feed fetching."""
        log_file = os.path.join(temp_dir, "test.log")
        processor = FeedProcessor(mock_openai_api_key, log_file)
        
        # Mock feedparser response
        mock_feed = Mock()
        mock_feed.status = 200
        mock_entry = Mock()
        mock_entry.get.side_effect = lambda key, default='': {
            'title': 'Test Article',
            'description': 'Test description',
            'link': 'https://example.com/article',
            'published': '2025-01-01T00:00:00Z'
        }.get(key, default)
        mock_feed.entries = [mock_entry]
        mock_parse.return_value = mock_feed
        
        # Override RSS_FEEDS for testing
        processor.RSS_FEEDS = ['https://test.com/feed.xml']
        
        entries = processor.fetch_feeds()
        
        assert len(entries) == 1
        assert entries[0]['title'] == 'Test Article'
        assert entries[0]['source'] == 'Unknown'  # test.com not in mapping
    
    @patch('feedparser.parse')
    def test_fetch_feeds_failure(self, mock_parse, temp_dir, mock_openai_api_key):
        """Test handling of feed fetch failures."""
        log_file = os.path.join(temp_dir, "test.log")
        processor = FeedProcessor(mock_openai_api_key, log_file)
        
        # Mock feedparser to raise exception
        mock_parse.side_effect = Exception("Connection failed")
        
        # Override RSS_FEEDS for testing
        processor.RSS_FEEDS = ['https://test.com/feed.xml']
        
        entries = processor.fetch_feeds()
        
        # Should return empty list on failure
        assert entries == []
        
        # Should log error
        with open(log_file, 'r') as f:
            log_content = f.read()
        assert "Connection failed" in log_content
    
    def test_fetch_feeds_returns_minimum_entries(self, temp_dir, mock_openai_api_key):
        """Test that feed parsing returns at least 1 entry per feed when successful."""
        log_file = os.path.join(temp_dir, "test.log")
        processor = FeedProcessor(mock_openai_api_key, log_file)
        
        with patch('feedparser.parse') as mock_parse:
            # Mock successful response with entries
            mock_feed = Mock()
            mock_feed.status = 200
            mock_entry1 = Mock()
            mock_entry1.get.side_effect = lambda key, default='': {
                'title': 'Test Article 1',
                'description': 'Test description 1',
                'link': 'https://example.com/article1',
                'published': '2025-01-01T00:00:00Z'
            }.get(key, default)
            mock_entry2 = Mock()
            mock_entry2.get.side_effect = lambda key, default='': {
                'title': 'Test Article 2',
                'description': 'Test description 2',
                'link': 'https://example.com/article2',
                'published': '2025-01-02T00:00:00Z'
            }.get(key, default)
            mock_feed.entries = [mock_entry1, mock_entry2]
            mock_parse.return_value = mock_feed
            
            # Test with one feed
            processor.RSS_FEEDS = ['https://test.com/feed.xml']
            entries = processor.fetch_feeds()
            
            # Should return at least 1 entry per feed
            assert len(entries) >= 1
            
            # Test with multiple feeds
            processor.RSS_FEEDS = ['https://test1.com/feed.xml', 'https://test2.com/feed.xml']
            entries = processor.fetch_feeds()
            
            # Should return at least 2 entries (1 per feed * 2 feeds)
            assert len(entries) >= 2


class TestSiteGenerator:
    """Test the SiteGenerator class."""
    
    def test_init(self, temp_dir):
        """Test SiteGenerator initialization."""
        templates_dir = os.path.join(temp_dir, "templates")
        os.makedirs(templates_dir)
        
        # Create minimal template
        template_path = os.path.join(templates_dir, "index.html")
        with open(template_path, 'w') as f:
            f.write("<html><body>{{ brief_date }}</body></html>")
        
        generator = SiteGenerator(templates_dir)
        assert generator.env is not None
    
    def test_generate_html(self, temp_dir, sample_brief_data):
        """Test HTML generation."""
        templates_dir = os.path.join(temp_dir, "templates")
        os.makedirs(templates_dir)
        
        # Create minimal template
        template_path = os.path.join(templates_dir, "index.html")
        with open(template_path, 'w') as f:
            f.write("<html><body><h1>{{ brief_date }}</h1><p>{{ total_items }} items</p></body></html>")
        
        generator = SiteGenerator(templates_dir)
        output_file = os.path.join(temp_dir, "output.html")
        
        generator.generate_html(sample_brief_data, output_file)
        
        # Check file was created
        assert Path(output_file).exists()
        
        # Check content
        with open(output_file, 'r') as f:
            content = f.read()
        
        assert "2025-01-01" in content
        assert "1 items" in content
    
    def test_generate_pdf(self, temp_dir, sample_brief_data):
        """Test PDF generation."""
        templates_dir = os.path.join(temp_dir, "templates")
        os.makedirs(templates_dir)
        
        # Create minimal template
        template_path = os.path.join(templates_dir, "pdf.html")
        with open(template_path, 'w') as f:
            f.write("""
            <html>
            <head><title>{{ brief_date }}</title></head>
            <body>
                <h1>{{ brief_date }}</h1>
                <p>{{ total_items }} items</p>
            </body>
            </html>
            """)
        
        generator = SiteGenerator(templates_dir)
        output_file = os.path.join(temp_dir, "output.pdf")
        
        # Mock WeasyPrint since it requires system dependencies
        with patch('weasyprint.HTML') as mock_html:
            mock_html.return_value.write_pdf = Mock()
            generator.generate_pdf(sample_brief_data, output_file)
            
            # Check that WeasyPrint was called
            mock_html.assert_called_once()
            mock_html.return_value.write_pdf.assert_called_once_with(output_file)


class TestLLMScorer:
    """Test the LLM scoring functionality."""
    
    def test_score_with_llm_returns_valid_response(self, temp_dir, mock_openai_api_key):
        """Test that LLM scorer returns float 0-5 and required texts."""
        log_file = os.path.join(temp_dir, "test.log")
        processor = FeedProcessor(mock_openai_api_key, log_file)
        
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '''
        {
            "score": 4.2,
            "summary": "This is a test summary that is exactly sixty words long and provides detailed information about the clinical research study including methodology, results, and potential implications for future treatment protocols and patient care.",
            "comment": "This clinical research finding has significant implications for patient treatment and care protocols in the future."
        }
        '''
        
        with patch.object(processor.openai_client.chat.completions, 'create', return_value=mock_response):
            test_entries = [
                {
                    'id': 'test-1',
                    'title': 'Test Clinical Trial',
                    'description': 'A clinical trial testing new treatment options.',
                    'link': 'https://example.com/article',
                    'pub_date': '2025-01-01T00:00:00Z',
                    'source': 'Test Source',
                    'brief_date': '2025-01-01'
                }
            ]
            
            scored_entries = processor.score_with_llm(test_entries)
            
            assert len(scored_entries) == 1
            entry = scored_entries[0]
            
            # Check score is float between 0-5
            assert isinstance(entry['score'], float)
            assert 0 <= entry['score'] <= 5
            
            # Check required text fields exist
            assert 'summary' in entry
            assert 'comment' in entry
            assert len(entry['summary']) > 0
            assert len(entry['comment']) > 0
            
            # Check specific values
            assert entry['score'] == 4.2
            assert "test summary" in entry['summary'].lower()
            assert "clinical research finding" in entry['comment'].lower()
    
    def test_score_with_llm_handles_invalid_response(self, temp_dir, mock_openai_api_key):
        """Test handling of invalid LLM responses."""
        log_file = os.path.join(temp_dir, "test.log")
        processor = FeedProcessor(mock_openai_api_key, log_file)
        
        # Mock OpenAI response with invalid JSON
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Invalid JSON response"
        
        with patch.object(processor.openai_client.chat.completions, 'create', return_value=mock_response):
            test_entries = [
                {
                    'id': 'test-1',
                    'title': 'Test Clinical Trial',
                    'description': 'A clinical trial testing new treatment options.',
                    'link': 'https://example.com/article',
                    'pub_date': '2025-01-01T00:00:00Z',
                    'source': 'Test Source',
                    'brief_date': '2025-01-01'
                }
            ]
            
            scored_entries = processor.score_with_llm(test_entries)
            
            # Should handle error gracefully and return empty list
            assert len(scored_entries) == 0
    
    def test_score_with_llm_api_error(self, temp_dir, mock_openai_api_key):
        """Test handling of OpenAI API errors."""
        log_file = os.path.join(temp_dir, "test.log")
        processor = FeedProcessor(mock_openai_api_key, log_file)
        
        # Mock OpenAI to raise exception
        with patch.object(processor.openai_client.chat.completions, 'create', side_effect=Exception("API Error")):
            test_entries = [
                {
                    'id': 'test-1',
                    'title': 'Test Clinical Trial',
                    'description': 'A clinical trial testing new treatment options.',
                    'link': 'https://example.com/article',
                    'pub_date': '2025-01-01T00:00:00Z',
                    'source': 'Test Source',
                    'brief_date': '2025-01-01'
                }
            ]
            
            scored_entries = processor.score_with_llm(test_entries)
            
            # Should handle error gracefully and return empty list
            assert len(scored_entries) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

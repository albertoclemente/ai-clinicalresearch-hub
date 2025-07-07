"""
Test configuration for Clinical Research Daily Brief
"""
import os
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield tmp_dir


@pytest.fixture
def mock_openai_api_key():
    """Mock OpenAI API key for testing."""
    return "test-api-key"


@pytest.fixture
def sample_feed_entry():
    """Sample RSS feed entry for testing."""
    return {
        'title': 'Test Clinical Trial Results',
        'description': 'A test clinical trial shows promising results for cancer treatment.',
        'link': 'https://example.com/article',
        'published': '2025-01-01T00:00:00Z',
        'id': 'test-entry-1'
    }


@pytest.fixture
def sample_brief_data():
    """Sample brief data for testing."""
    return {
        'brief_date': '2025-01-01',
        'generated_at': '2025-01-01T12:00:00Z',
        'items': [
            {
                'id': 'test-item-1',
                'title': 'Test Article Title',
                'summary': 'This is a test summary of the article.',
                'impact': 'This has significant impact.',
                'score': 4.5,
                'source': 'Test Source',
                'pub_date': '2025-01-01T00:00:00Z',
                'link': 'https://example.com/article',
                'brief_date': '2025-01-01'
            }
        ],
        'total_items': 1
    }

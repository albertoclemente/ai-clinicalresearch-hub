#!/usr/bin/env python3
"""
Test script for AI pipeline without OpenAI dependency
"""

import json
from datetime import datetime, timezone

# Mock data representing articles from RSS feeds
mock_articles = [
    {
        'id': '1',
        'title': 'Machine Learning Models Improve Drug Discovery in Phase II Trials',
        'description': 'Researchers use AI algorithms to predict compound efficacy in clinical trials, reducing development time by 30%.',
        'link': 'https://example.com/ai-drug-discovery',
        'pub_date': datetime.now(timezone.utc).isoformat(),
        'source': 'Nature Medicine',
        'brief_date': '2025-07-08',
        'is_ai_related': True,
        'summary': 'AI algorithms demonstrate 30% reduction in drug development time by predicting compound efficacy in Phase II trials.',
        'comment': 'This breakthrough highlights AI\'s potential to revolutionize pharmaceutical R&D. However, questions remain about regulatory acceptance and validation of AI-predicted outcomes.'
    },
    {
        'id': '2', 
        'title': 'New Cancer Treatment Shows Promise in Clinical Trial',
        'description': 'Traditional chemotherapy approach shows positive results in treating lung cancer patients.',
        'link': 'https://example.com/cancer-treatment',
        'pub_date': datetime.now(timezone.utc).isoformat(),
        'source': 'NEJM',
        'brief_date': '2025-07-08',
        'is_ai_related': False  # This would be filtered out
    },
    {
        'id': '3',
        'title': 'Digital Health App Improves Patient Adherence in Diabetes Management',
        'description': 'Mobile application using behavioral analytics increases medication compliance by 45% in diabetic patients.',
        'link': 'https://example.com/digital-health',
        'pub_date': datetime.now(timezone.utc).isoformat(),
        'source': 'BioPharma Dive',
        'brief_date': '2025-07-08',
        'is_ai_related': True,
        'summary': 'Digital health app leveraging behavioral analytics achieves 45% improvement in medication adherence among diabetes patients.',
        'comment': 'This demonstrates the power of digital therapeutics in chronic disease management. Key questions include data privacy, long-term sustainability, and integration with existing healthcare systems.'
    }
]

def test_ai_filtering():
    """Test the AI filtering logic"""
    print("AI in Clinical Research Bi-Weekly Brief - Test Run")
    print("=" * 60)
    
    # Filter only AI-related articles
    ai_articles = [article for article in mock_articles if article.get('is_ai_related', False)]
    
    print(f"Total articles processed: {len(mock_articles)}")
    print(f"AI-related articles found: {len(ai_articles)}")
    print()
    
    # Display the AI articles
    for i, article in enumerate(ai_articles, 1):
        print(f"Article {i}:")
        print(f"Title: {article['title']}")
        print(f"Source: {article['source']}")
        print(f"Summary: {article['summary']}")
        print(f"Comment: {article['comment']}")
        print("-" * 60)
    
    # Save to JSON for testing
    brief_data = {
        'brief_date': '2025-07-08',
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'items': ai_articles,
        'total_items': len(ai_articles)
    }
    
    with open('test_ai_brief.json', 'w') as f:
        json.dump(brief_data, f, indent=2)
    
    print(f"Test data saved to test_ai_brief.json")

if __name__ == "__main__":
    test_ai_filtering()

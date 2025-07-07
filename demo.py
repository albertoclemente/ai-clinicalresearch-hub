#!/usr/bin/env python3
"""
Demo script showing the Clinical Research Daily Brief system in action.
This creates sample data to demonstrate the full pipeline without requiring API keys.
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path

# Sample RSS feed data (simulating what would come from real feeds)
SAMPLE_FEED_DATA = [
    {
        'id': 'sample-1',
        'title': 'Phase III Trial Shows Promising Results for Novel Oncology Treatment',
        'description': 'A randomized controlled trial involving 1,200 patients demonstrates significant improvement in overall survival for patients with advanced solid tumors.',
        'summary': 'Phase III clinical trial of 1,200 patients shows novel oncology treatment improves overall survival by 35% compared to standard care, with manageable safety profile and potential regulatory submission.',
        'comment': 'Major breakthrough could transform treatment options for advanced cancer patients and establish new standard of care protocols.',
        'score': 4.8,
        'source': 'ClinicalTrials.gov',
        'pub_date': '2025-07-07T08:00:00Z',
        'link': 'https://clinicaltrials.gov/study/NCT12345678',
        'brief_date': '2025-07-07'
    },
    {
        'id': 'sample-2',
        'title': 'FDA Approves First-in-Class Treatment for Rare Neurological Disorder',
        'description': 'The FDA has granted accelerated approval for a breakthrough therapy targeting a rare genetic condition affecting motor neurons.',
        'summary': 'FDA grants accelerated approval for first-in-class gene therapy targeting rare motor neuron disease, offering hope for 5,000 patients annually with previously untreatable condition.',
        'comment': 'Historic approval opens new therapeutic pathway for rare disease patients and validates innovative gene therapy approaches.',
        'score': 4.6,
        'source': 'FDA',
        'pub_date': '2025-07-07T10:30:00Z',
        'link': 'https://fda.gov/news-events/press-announcements/sample-approval',
        'brief_date': '2025-07-07'
    },
    {
        'id': 'sample-3',
        'title': 'Large-Scale Cardiovascular Prevention Study Results Published',
        'description': 'Multi-center study of 15,000 participants reveals new insights into cardiovascular risk prevention strategies.',
        'summary': 'Landmark cardiovascular prevention study of 15,000 participants demonstrates 28% reduction in major adverse cardiac events through novel combination therapy approach over 3.2 years.',
        'comment': 'Results could reshape cardiovascular prevention guidelines and reduce heart disease burden affecting millions of patients worldwide.',
        'score': 4.3,
        'source': 'NEJM',
        'pub_date': '2025-07-07T12:15:00Z',
        'link': 'https://nejm.org/doi/full/10.1056/NEJMoa2025sample',
        'brief_date': '2025-07-07'
    },
    {
        'id': 'sample-4',
        'title': 'Biosimilar Approval Pathway Updated to Streamline Patient Access',
        'description': 'New regulatory guidance aims to accelerate biosimilar approvals while maintaining safety standards.',
        'summary': 'Updated FDA biosimilar guidance streamlines approval pathway with new analytical methods, potentially reducing development timelines by 18 months while maintaining rigorous safety standards.',
        'comment': 'Faster biosimilar approvals could significantly reduce healthcare costs and improve patient access to critical biological therapies.',
        'score': 3.9,
        'source': 'RAPS',
        'pub_date': '2025-07-07T14:45:00Z',
        'link': 'https://raps.org/news-and-articles/sample-biosimilar-guidance',
        'brief_date': '2025-07-07'
    },
    {
        'id': 'sample-5',
        'title': 'AI-Driven Clinical Trial Design Shows 40% Faster Patient Recruitment',
        'description': 'Artificial intelligence platform optimizes clinical trial protocols and patient matching algorithms.',
        'summary': 'AI-powered clinical trial platform demonstrates 40% faster patient recruitment and 25% improved retention rates across multiple Phase II oncology studies with enhanced protocol optimization.',
        'comment': 'Revolutionary approach could accelerate drug development timelines and reduce clinical trial costs while improving patient outcomes.',
        'score': 4.1,
        'source': 'Nature Medicine',
        'pub_date': '2025-07-07T16:20:00Z',
        'link': 'https://nature.com/articles/s41591-025-sample',
        'brief_date': '2025-07-07'
    },
    {
        'id': 'sample-6',
        'title': 'Digital Health Platform Integration in Clinical Research Workflow',
        'description': 'New platform enables seamless integration of digital health data into clinical research protocols.',
        'summary': 'Comprehensive digital health platform integrates wearable devices, patient-reported outcomes, and real-world evidence into clinical trials, improving data quality and patient engagement significantly.',
        'comment': 'Digital integration transforms clinical research methodology and enhances patient-centric trial design for better therapeutic development.',
        'score': 3.7,
        'source': 'BioPharma Dive',
        'pub_date': '2025-07-07T18:00:00Z',
        'link': 'https://biopharmadive.com/news/sample-digital-health-platform',
        'brief_date': '2025-07-07'
    },
    {
        'id': 'sample-7',
        'title': 'Global Health Initiative Launches Multi-Country Infectious Disease Trial',
        'description': 'International collaboration begins Phase III trial for next-generation vaccine platform.',
        'summary': 'Global health consortium launches Phase III trial across 20 countries testing next-generation vaccine platform against emerging infectious diseases with innovative delivery mechanisms.',
        'comment': 'International collaboration strengthens pandemic preparedness and could provide rapid response capabilities for future health emergencies.',
        'score': 4.0,
        'source': 'NIH',
        'pub_date': '2025-07-07T20:30:00Z',
        'link': 'https://clinicalcenter.nih.gov/news/sample-global-health-trial',
        'brief_date': '2025-07-07'
    },
    {
        'id': 'sample-8',
        'title': 'Pediatric Cancer Treatment Shows Breakthrough Results in Early Trials',
        'description': 'Novel immunotherapy approach demonstrates exceptional response rates in pediatric solid tumors.',
        'summary': 'Groundbreaking pediatric immunotherapy trial achieves 82% response rate in children with relapsed solid tumors, offering new hope for previously treatment-resistant pediatric cancers.',
        'comment': 'Exceptional results provide new treatment option for children with limited therapeutic alternatives and advances pediatric cancer care.',
        'score': 4.4,
        'source': 'ClinicalTrials.gov',
        'pub_date': '2025-07-07T22:10:00Z',
        'link': 'https://clinicaltrials.gov/study/NCT87654321',
        'brief_date': '2025-07-07'
    }
]


def generate_demo_brief():
    """Generate a complete demo brief with sample data."""
    print("🔬 Clinical Research Daily Brief - Demo Generation")
    print("=" * 60)
    
    # Create directories
    for directory in ['briefs', 'logs', 'site']:
        Path(directory).mkdir(exist_ok=True)
        
    brief_date = '2025-07-07'
    
    # Step 1: Filter and sort sample data (simulate top item selection)
    print("1. Selecting top articles...")
    top_items = sorted(SAMPLE_FEED_DATA, key=lambda x: x['score'], reverse=True)[:8]
    print(f"   Selected {len(top_items)} articles with scores ≥ 3.0")
    
    # Step 2: Create brief data structure
    brief_data = {
        'brief_date': brief_date,
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'items': top_items,
        'total_items': len(top_items)
    }
    
    # Step 3: Save JSON file
    json_file = f'briefs/{brief_date}.json'
    print(f"2. Saving brief data to {json_file}...")
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(brief_data, f, indent=2, ensure_ascii=False)
    
    # Step 4: Generate HTML
    print("3. Generating HTML page...")
    from jinja2 import Environment, FileSystemLoader
    
    env = Environment(loader=FileSystemLoader('templates'))
    template = env.get_template('index.html')
    
    html_content = template.render(**brief_data)
    
    html_file = 'site/index.html'
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    # Step 5: Create log entry
    log_file = f'logs/{brief_date}.log'
    print(f"4. Creating log file {log_file}...")
    
    log_entries = []
    for i, source in enumerate([
        'clinicaltrials.gov', 'fda.gov', 'nih.gov', 'nature.com', 'nejm.org', 'biopharmadive.com', 'raps.org',
        'clinicalresearchnewsonline.com', 'endpts.com', 'centerwatch.com', 'appliedclinicaltrialsonline.com',
        'clinicaltrialsarena.com', 'outsourcing-pharma.com', 'acrpnet.org'
    ]):
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "feed_url": f"https://{source}/rss.xml",
            "http_status": 200,
            "error": None
        }
        log_entries.append(json.dumps(log_entry))
    
    with open(log_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(log_entries))
    
    # Step 6: Display results
    print("\n✅ Demo brief generated successfully!")
    print("\nGenerated files:")
    print(f"  📄 {json_file} - Brief data")
    print(f"  🌐 {html_file} - Web page")
    print(f"  📋 {log_file} - Processing logs")
    
    print(f"\n📊 Brief Summary ({brief_date}):")
    print(f"  • Total articles: {len(top_items)}")
    print(f"  • Highest score: {max(item['score'] for item in top_items)}")
    print(f"  • Average score: {sum(item['score'] for item in top_items) / len(top_items):.1f}")
    
    print("\n🏆 Top 3 Articles:")
    for i, item in enumerate(top_items[:3], 1):
        print(f"  {i}. {item['title'][:60]}...")
        print(f"     Score: {item['score']}/5 | Source: {item['source']}")
    
    print(f"\n🌐 View the generated site:")
    print(f"  file://{os.path.abspath(html_file)}")
    
    return brief_data


if __name__ == "__main__":
    generate_demo_brief()

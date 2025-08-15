# AI-Powered Clinical Research Intelligence Hub

An advanced automated pipeline that discovers, analyzes, and curates cutting-edge AI applications in clinical research using **Qwen LLM** (via OpenRouter), featuring a premium glassmorphism web interface with comprehensive UI/UX enhancements.

## 🚀 Recent Major Updates (August 2025)

### **🎨 Premium UI Design & Enhanced User Experience**
- **Complete Visual Transformation**: Modern glassmorphism design with gradient backgrounds, floating blur effects, and semi-transparent cards
- **Curiosity-Driven Interface**: Enhanced hero section with animated elements and interactive search designed to encourage exploration
- **Complete Filter System**: All 6 AI technology categories from pipeline now available as functional filter pills
- **Enhanced Accessibility**: Full WCAG compliance with screen reader support, keyboard navigation, and semantic HTML
- **Advanced UI/UX Features**: Debounced search, URL state management, copy-to-clipboard, back-to-top navigation
- **Template Synchronization**: Perfect alignment between template filters and pipeline AI categorization

### **🔧 Technical Enhancements & Production Readiness**
- **Token Bucket Rate Limiting**: Sophisticated API throttling to prevent 429 errors and improve reliability
- **Enhanced HTTP Retries**: Exponential backoff with jitter for all API calls
- **XSS Protection**: Safe search highlighting with regex and HTML escaping
- **Frontend UI/UX Improvements**: 14 comprehensive enhancements implemented including:
  - Debounced search with 150ms delay
  - Keyboard navigation (/ to focus, Escape to clear)
  - Skip-to-content accessibility links
  - Reduced motion support for better battery life
  - URL state persistence for shareable links
  - Advanced sorting controls (newest/oldest/source)
  - Live region announcements for screen readers
  - Copy link functionality with fallbacks
  - Back-to-top button with smooth scrolling
  - Enhanced semantic HTML with time elements
  - Focus-visible styles for keyboard navigation
  - Improved color contrast for WCAG compliance

### **🛡️ Production Robustness**
- **Atomic File Writes**: Prevents corrupted output files
- **Schema Validation**: Pydantic models ensure data integrity
- **Comprehensive Error Handling**: Graceful degradation for API failures
- **Enhanced Logging**: Detailed monitoring for production deployments

## ✨ Core Features

### Intelligence Pipeline
- **Automated Content Discovery**: Monitors 12+ trusted sources including PubMed, Clinical Trials gov, and specialized journals
- **AI-Powered Analysis**: Uses **Qwen LLM (via OpenRouter)** to analyze and categorize articles by 6 specific AI technology types
- **Smart Filtering**: Intelligent filtering to identify content specifically related to AI applications in clinical research
- **Multi-format Output**: Generates both JSON data and premium styled HTML presentations
- **Daily Automation**: Production-ready for unattended GitHub Actions deployment

### Premium Web Interface
- **Glassmorphism Design**: Modern UI with frosted glass effects, animated gradients, and floating elements
- **Interactive Filtering**: Real-time filtering by 6 AI technology categories with visual filter pills
- **Advanced Search**: Debounced search with highlighting, XSS protection, and multi-criteria filtering
- **Responsive Design**: Optimized for desktop, tablet, and mobile devices with accessibility features
- **Keyboard Navigation**: Full keyboard accessibility with GitHub-style shortcuts

## 🧠 AI Technology Categories

The system provides comprehensive coverage across 6 key AI domains:

1. **🤖 Generative AI** - LLMs, ChatGPT, text generation applications
2. **💬 Natural Language Processing** - Text analysis, clinical notes processing
3. **🧠 Machine Learning** - Predictive models, algorithms, ML techniques
4. **📱 Digital Health** - Health apps, digital therapeutics, connected devices
5. **🎯 Trial Optimization** - Clinical trial design, patient recruitment, protocol optimization
6. **⚖️ AI Ethics** - Bias, fairness, transparency, responsible AI implementation

Each article is analyzed using **Qwen LLM** to determine relevance, extract key insights, categorize by technology type, and generate concise summaries optimized for discovery.

## 🛠️ Technology Stack

### Backend Pipeline
- **Python 3.8+** for core pipeline
- **Qwen LLM (via OpenRouter)** for content analysis
- **Beautiful Soup** for web scraping
- **Requests** for HTTP operations
- **Jinja2** for HTML templating

### Frontend Interface
- **Alpine.js 3.x** for reactive interactions
- **Tailwind CSS** for utility-first styling
- **Custom CSS** for glassmorphism effects and animations
- **Google Fonts** (Geist & JetBrains Mono) for typography
- **Responsive Design** with mobile-first approach

## 📊 Data Sources

The pipeline monitors these authoritative sources:
- PubMed Central (PMC)
- Clinical Trials Database
- Nature Medicine
- NEJM AI
- The Lancet Digital Health
- JMIR Medical Informatics
- Journal of Medical Internet Research
- NPJ Digital Medicine
- And more specialized publications

## 📈 Output

The pipeline generates:
- **JSON briefs** with structured data and AI categorization (`briefs/YYYY-MM-DD.json`)
- **Premium HTML presentations** with interactive filtering (`site/index.html`)
- **Detailed logs** for monitoring and debugging (`logs/YYYY-MM-DD.log`)

## 🔧 Setup & Installation

1. **Clone the repository**
```bash
git clone https://github.com/albertoclemente/gen-ai-clinical-trials-watch.git
cd gen-ai-clinical-trials-watch
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set environment variables**
```bash
export OPENROUTER_API_KEY="your-openrouter-api-key-here"
```

4. **Run the pipeline**
```bash
python pipeline.py
```

Note: The pipeline automatically generates the HTML interface, so there's no need for a separate `generate_html.py` step.

## 🎨 Premium Web Interface Features

### Design Philosophy
- **Curiosity-Driven**: Interface designed to encourage exploration of AI breakthroughs
- **Visual Hierarchy**: Clear information architecture highlighting key insights
- **Engagement Focus**: Interactive elements that make discovery enjoyable
- **Professional Aesthetics**: Clean, modern design suitable for research professionals

### Interactive Features
- **Smart Filter Pills**: 7 filter options (All + 6 AI categories) with visual feedback
- **Real-time Search**: Instant filtering with search term highlighting
- **Responsive Cards**: Hover effects and smooth transitions for article cards
- **Category Badges**: Color-coded AI technology indicators with gradients
- **Stats Display**: Dynamic counters and date information
- **Smooth Scrolling**: Enhanced navigation between sections

### Technical Implementation
- **Template Synchronization**: Filter system perfectly aligned with pipeline AI categorization
- **Performance Optimized**: Efficient Alpine.js reactivity without framework overhead
- **Cross-browser Compatible**: Tested across modern browsers
- **Accessibility Focused**: Proper semantic HTML and keyboard navigation
- **Mobile Responsive**: Optimized experience across all device sizes

## 📅 Automation

The pipeline can be automated using GitHub Actions. The workflow file runs daily and:
- Executes the scraping and analysis pipeline
- Generates new brief files with AI categorization
- Creates premium HTML presentation
- Commits results to the repository
- Deploys the interactive web interface

## 📊 Typical AI Technology Distribution

Based on current data analysis:
- **Generative AI** (🤖) - 25% of discoveries typically
- **Machine Learning** (🧠) - 30% of discoveries typically  
- **Natural Language Processing** (💬) - 20% of discoveries typically
- **Digital Health** (📱) - 15% of discoveries typically
- **Trial Optimization** (🎯) - 7% of discoveries typically
- **AI Ethics** (⚖️) - 3% of discoveries typically

## 📁 Repository Structure

```
clinical_research_daily_brief/
├── briefs/                                 # Generated content
│   └── YYYY-MM-DD.json                    # Daily brief data
├── logs/                                   # Processing logs
│   └── YYYY-MM-DD.log                     # Detailed logs
├── site/                                   # Static website output
│   ├── index.html                          # Generated main page
│   ├── styles.css                          # Additional styling
│   └── assets/                             # Static assets
├── templates/                              # Jinja2 templates
│   └── index.html                          # Main page template with premium UI
├── pipeline.py                             # Main processing script
├── qwen_client.py                          # Qwen LLM client wrapper
├── generate_html.py                        # Standalone HTML generation utility
├── requirements.txt                        # Python dependencies
├── environment.yml                         # Conda environment
├── FRONTEND_IMPROVEMENTS_IMPLEMENTED.md    # Frontend enhancement documentation
├── AMELIORATIONS_IMPLEMENTED.md           # Production robustness documentation
├── IMPROVEMENTS_IMPLEMENTED.md            # General improvements documentation
└── README.md                              # This file
```

## 🔄 Recent Improvements Timeline

### August 2025 - Complete UI Overhaul
1. **Premium Glassmorphism Design**: Complete visual transformation with modern UI
2. **Filter System Enhancement**: Fixed non-functional filter pills and added missing AI categories
3. **Template Synchronization**: Aligned all filters with pipeline AI tag definitions
4. **UI Cleanup**: Removed distracting trending insights bars and unnecessary statistics
5. **Enhanced Interactivity**: Improved search functionality and responsive design

### Previous Updates
- **Dynamic Summary Generation**: 8 rotating writing styles
- **Enhanced Quality Filtering**: Multi-tier content validation
- **Extended Search Coverage**: 60-day rolling window
- **Performance Optimization**: Faster loading and better responsiveness

## 🚦 Testing & Validation

The system includes comprehensive testing for:
- Filter functionality across all 6 AI categories
- Template-pipeline synchronization
- Search and highlighting features
- Responsive design across devices
- Content quality and relevance

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🔗 Links

- [GitHub Repository](https://github.com/albertoclemente/gen-ai-clinical-trials-watch)
- [Frontend Improvements Documentation](./FRONTEND_IMPROVEMENTS_IMPLEMENTED.md)
- [Production Robustness Documentation](./AMELIORATIONS_IMPLEMENTED.md)
- [General Improvements Documentation](./IMPROVEMENTS_IMPLEMENTED.md)

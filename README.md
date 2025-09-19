# AI-Powered Clinical Research Intelligence Hub

An advanced automated pipeline that discovers, analyzes, and curates cutting-edge AI applications in clinical research using **Qwen LLM** (via OpenRouter), featuring a premium glassmorphism web interface with comprehensive UI/UX enhancements.

## 🚀 Recent Major Updates (August 17, 2025)

### **⏰ Automated Daily Scheduling**
- **Weekday Automation**: Pipeline now runs automatically Monday-Friday at 5:00 AM Central European Time
- **GitHub Actions Integration**: Scheduled workflow ensures daily content updates without manual intervention
- **Timezone Awareness**: Proper CET/CEST handling for consistent 5 AM local time execution
- **Dual Trigger Support**: Maintains manual trigger option alongside automated scheduling
- **Enhanced Logging**: Clear distinction between automated and manual runs in deployment logs

### **🔧 Previous Refinements & Production Optimization** (August 16, 2025)
- **Search Interface Polish**: Fixed search icon display issue replacing UTF-8 replacement character (�) with proper 🔍 emoji
- **Production Pipeline Run**: Successfully processed 180 articles, identified 16 AI-relevant discoveries with excellent cost efficiency ($0.10)
- **Enhanced Content Curation**: Qwen LLM filtering achieved 8.9% precision rate from comprehensive source network
- **Rate Limiting Optimization**: Successfully handled Google API constraints with exponential backoff strategy
- **Template Persistence**: All UI improvements now survive automated pipeline regeneration

### **🎨 Premium UI Design & Enhanced User Experience**
- **Complete Visual Transformation**: Modern glassmorphism design with gradient backgrounds, floating blur effects, and semi-transparent cards
- **Curiosity-Driven Interface**: Enhanced hero section with animated elements and interactive search designed to encourage exploration
- **Complete Filter System**: All 6 AI technology categories from pipeline now available as functional filter pills
- **Mobile-First Optimization**: Comprehensive mobile responsiveness with optimized layouts, horizontal scrolling category pills, and iOS safe-area support
- **Enhanced Accessibility**: Full WCAG compliance with screen reader support, keyboard navigation, and semantic HTML
- **Advanced UI/UX Features**: Debounced search, URL state management, copy-to-clipboard, back-to-top navigation, momentum scrolling
- **Cross-Device Excellence**: Perfect functionality across desktop, tablet, and mobile with touch-optimized interactions
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
  - Mobile-optimized layouts with horizontal scrolling category pills
  - iOS safe-area support and momentum scrolling for optimal mobile experience

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
- **Accurate Publication Dates**: Advanced date parsing with support for relative dates ("2 days ago") and multiple metadata fields
- **Enhanced Title Extraction**: Smart title handling with truncation detection and intelligent completion for professional presentation
- **Multi-format Output**: Generates both JSON data and premium styled HTML presentations
- **Daily Automation**: Runs automatically Monday-Friday at 5:00 AM CET via GitHub Actions with production-ready deployment

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
- **Tailwind CSS** for utility-first styling with mobile-first responsive design
- **Custom CSS** for glassmorphism effects, animations, and momentum scrolling
- **Google Fonts** (Geist & JetBrains Mono) for typography
- **Mobile-Optimized Design** with iOS safe-area support and horizontal scrolling interfaces

## 📊 Latest Pipeline Performance (Aug 16, 2025)

### Content Discovery Metrics
- **Total Articles Processed**: 180 from comprehensive source network
- **AI-Relevant Articles Identified**: 16 high-quality discoveries (8.9% precision)
- **Cost Efficiency**: $0.10 per complete content curation run
- **Source Distribution**: Google Scholar, PubMed (20 API calls), Europe PMC, Semantic Scholar, RSS feeds
- **Rate Limiting**: Successfully managed API constraints with exponential backoff

### Quality Assurance
- **Qwen LLM Filtering**: Effective identification of AI-clinical research intersections
- **Source Diversity**: Multi-platform content acquisition ensuring comprehensive coverage
- **Template Consistency**: All UI improvements persist through automated regeneration
- **User Experience**: Professional search interface with proper icon display

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
git clone https://github.com/albertoclemente/ai-clinicalresearch-hub.git
cd ai-clinicalresearch-hub
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set environment variables (local runs)**
```bash
export OPENROUTER_API_KEY="your-openrouter-api-key-here"
# Optional (Google Custom Search for broader discovery)
export GOOGLE_API_KEY="your-google-api-key"
export GOOGLE_CX="your-google-cse-id"   # aka CSE ID
# Optional (privacy-friendly site analytics)
export GOATCOUNTER_URL="https://YOURCODE.goatcounter.com/count"
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
- **Smart Filter Pills**: 7 filter options (All + 6 AI categories) with horizontal scrolling and visual feedback
- **Real-time Search**: Instant filtering with search term highlighting and debounced input
- **Responsive Cards**: Hover effects and smooth transitions for article cards
- **Category Badges**: Color-coded AI technology indicators with gradients
- **Stats Display**: Dynamic counters and date information
- **Mobile Navigation**: Optimized touch interactions with momentum scrolling and iOS safe-area support
- **Smooth Scrolling**: Enhanced navigation between sections with reduced motion support

### Technical Implementation
- **Template Synchronization**: Filter system perfectly aligned with pipeline AI categorization
- **Performance Optimized**: Efficient Alpine.js reactivity without framework overhead
- **Cross-browser Compatible**: Tested across modern browsers with fallback support
- **Accessibility Focused**: Proper semantic HTML, keyboard navigation, and screen reader support
- **Mobile Excellence**: Fully responsive with iOS safe-area support, horizontal scrolling, and momentum scrolling
- **Touch Optimized**: Enhanced mobile interactions with proper viewport handling and reduced motion support

## 📅 Deployment & Automation

### Automated Daily Runs
The pipeline runs automatically **Monday through Friday at 5:00 AM Central European Time** via GitHub Actions.

**Schedule Details:**
- **Frequency**: Weekdays only (Monday-Friday)
- **Time**: 5:00 AM CET/CEST (3:00 AM UTC)
- **Timezone**: Central European Time with daylight saving awareness
- **Output**: Fresh daily brief with latest AI clinical research discoveries

### Manual Deployment (GitHub Pages)

For manual runs or initial setup:

1) Enable Pages
- Settings → Pages → Source: "Deploy from a branch"
- Branch: `gh-pages`, Folder: `/ (root)`

2) Add repository secrets (Settings → Secrets and variables → Actions)
- `OPENROUTER_API_KEY` (required)
- `GOOGLE_API_KEY` (optional)
- `GOOGLE_CX` (preferred) or `GOOGLE_CSE_ID` (optional)
- `GOATCOUNTER_URL` (optional, for analytics; format: https://YOURCODE.goatcounter.com/count)

3) Run the workflow manually (if needed)
- Go to the Actions tab → "🔬 AI Clinical Research Intelligence Hub - Daily Automation" → Run workflow

The workflow generates the brief, builds `site/index.html`, and publishes to the `gh-pages` branch.
Your site will be available at:
https://albertoclemente.github.io/ai-clinicalresearch-hub/

**Automated vs Manual Runs:**
- **Automated**: Runs daily at 5 AM CET Monday-Friday automatically
- **Manual**: Can be triggered anytime via GitHub Actions interface
- **Both**: Generate identical output with clear logging of trigger type

Note: The workflow uses Python 3.9 and installs dependencies from `requirements.txt` on each run.

## 📈 Analytics (optional, GoatCounter)

Privacy-friendly analytics are supported via GoatCounter:

- Create a GoatCounter site; copy the `data-goatcounter` URL (looks like `https://YOURCODE.goatcounter.com/count`).
- Add repo secret `GOATCOUNTER_URL` with that value (no quotes).
- On deploy, the template injects:
  `<script data-goatcounter="{{ GOATCOUNTER_URL }}" async src="https://gc.zgo.at/count.js"></script>`

Verify after deploy: View Source on the live page and search for `gc.zgo.at` or `data-goatcounter`.

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
ai-clinicalresearch-hub/
├── briefs/                 # Generated content (YYYY-MM-DD.json)
├── logs/                   # Processing logs (YYYY-MM-DD.log)
├── site/                   # Static website output (published to gh-pages)
│   ├── index.html
│   └── styles.css
├── templates/              # Jinja2 templates (main UI)
│   ├── index.html
│   └── pdf.html
├── .github/workflows/
│   └── deploy.yml          # Manual GitHub Pages deployment workflow
├── pipeline.py             # Main processing script
├── qwen_client.py          # Qwen LLM client wrapper (OpenRouter)
├── requirements.txt        # Python dependencies
├── environment.yml         # Optional conda environment
├── IMPROVEMENTS_IMPLEMENTED.md
├── targeted_improvements.md
└── README.md
```

## 🔄 Recent Improvements Timeline

### August 18, 2025 - Mobile UI/UX Excellence & Cross-Device Optimization
1. **Hero Section Optimization**: Refined viewport height handling (min-h-[80vh] sm:min-h-[85vh]) to eliminate mobile white space issues
2. **Search Interface Enhancement**: Improved mobile visibility with enhanced background opacity (bg-white/90) for better contrast
3. **Category Pills Redesign**: Implemented horizontal scrolling with momentum scrolling for optimal mobile category navigation
4. **iOS Safe-Area Support**: Added viewport-fit=cover and safe-area padding for seamless iPhone experience  
5. **Touch Interaction Optimization**: Enhanced mobile touch targets and scroll behavior for improved usability
6. **Cross-Device Testing**: Comprehensive mobile DevTools validation ensuring consistent experience across all screen sizes

### August 17, 2025 - Daily Automation & Scheduling
1. **Automated Weekday Runs**: GitHub Actions scheduled for Monday-Friday at 5:00 AM CET
2. **Timezone Handling**: Proper CET/CEST awareness with daylight saving time support
3. **Dual Trigger Support**: Maintains both automated schedule and manual trigger options
4. **Enhanced Workflow**: Updated deployment messages and logging for automated runs
5. **Production Ready**: Fully automated daily content generation and deployment

### August 16, 2025 - Search Interface Polish & Production Optimization
1. **Search Icon Fix**: Resolved UTF-8 replacement character (�) with proper 🔍 emoji display
2. **Production Run**: Successful pipeline execution processing 180 articles → 16 AI discoveries
3. **Cost Optimization**: Maintained excellent efficiency at $0.10 per comprehensive content run
4. **Template Persistence**: Ensured all UI improvements survive automated regeneration
5. **Rate Limiting**: Enhanced API throttling with exponential backoff for reliability

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

- [GitHub Repository](https://github.com/albertoclemente/ai-clinicalresearch-hub)
- [Live Site](https://albertoclemente.github.io/ai-clinicalresearch-hub/)
- [Improvements Log](./IMPROVEMENTS_IMPLEMENTED.md)

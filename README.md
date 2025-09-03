# ContractCritic - AI-Powered Contract Review Platform

![ContractCritic Logo](design-assets/contractcritic_logo.png)

A comprehensive micro SaaS application that provides AI-powered contract review for freelancers, solopreneurs, and small business owners.

## 📁 Project Organization

This project is organized into clear, separate folders:

```
ContractCritic/
├── backend/                    # 🔧 Flask Backend Application
├── frontend/                   # ⚛️ React Frontend Application  
├── documentation/              # 📚 Complete Documentation
├── design-assets/              # 🎨 UI/UX Design Assets
├── tests/                      # 🧪 Test Suite
└── README.md                   # This file
```

## 🚀 Quick Start

### 1. Backend Setup
```bash
cd backend/
source venv/bin/activate
pip install -r requirements.txt
export OPENAI_API_KEY=your_openai_api_key_here
python src/main.py
```
Backend runs on: http://localhost:5000

### 2. Frontend Setup (New Terminal)
```bash
cd frontend/
pnpm install
pnpm run dev
```
Frontend runs on: http://localhost:5173

### 3. Test the Application
- Open http://localhost:5173 in your browser
- Upload a contract file (PDF, DOCX, DOC, TXT)
- Click "Analyze Contract" to see AI insights

## 📂 Folder Details

### 🔧 **backend/** - Flask API Server
- `src/models/` - Database models (User, Contract, Analysis)
- `src/routes/` - API endpoints for contracts and analysis
- `src/services/` - Business logic and AI integration
- `src/static/` - Built frontend files (for production deployment)
- `requirements.txt` - Python dependencies
- `simple_test.py` - Backend test suite

### ⚛️ **frontend/** - React Web Application
- `src/components/` - React components (Dashboard, Upload, Analysis, etc.)
- `src/hooks/` - Custom React hooks
- `dist/` - Production build output
- `package.json` - Node.js dependencies
- `index.html` - HTML entry point

### 📚 **documentation/** - Complete Documentation
- `README.md` - Detailed project documentation
- `deployment_guide.md` - Production deployment instructions
- `technical_architecture.md` - System architecture and AI models
- `market_research_findings.md` - Business analysis and market research
- `design_concept.md` - UI/UX design guidelines
- `todo.md` - Development progress log

### 🎨 **design-assets/** - UI/UX Design Files
- `contractcritic_logo.png` - Professional logo
- `dashboard_mockup.png` - Dashboard interface design
- `contract_analysis_mockup.png` - Analysis results interface
- `mobile_mockup.png` - Mobile-responsive design
- `app_icon.png` - Application icon

### 🧪 **tests/** - Test Suite
- `integration_test.py` - Full application integration tests
- `test_backend.py` - Backend API tests

## ✨ Key Features

### 🤖 AI-Powered Analysis
- Smart contract review using OpenAI GPT models
- Risk scoring (0-100 scale) with color-coded visualization
- Plain English summaries of complex legal terms
- Actionable recommendations and negotiation points

### 📊 Professional Dashboard
- Contract overview with key metrics and statistics
- Risk distribution visualization with progress bars
- Recent activity tracking and status updates
- Quick action shortcuts for common tasks

### 📁 Advanced File Management
- Multi-format support (PDF, DOCX, DOC, TXT)
- Drag-and-drop upload with progress tracking
- Secure file handling and storage
- Contract list with filtering and search capabilities

### 🎨 Modern Interface
- Responsive design for desktop and mobile devices
- Professional UI with Tailwind CSS and shadcn/ui
- Intuitive navigation with sidebar routing
- Real-time status updates during analysis

## 🔑 Environment Setup

Required environment variable:
```bash
export OPENAI_API_KEY=your_openai_api_key_here
```

Get your API key from: https://platform.openai.com/api-keys

## 🧪 Testing

Run the test suite:
```bash
cd tests/
python integration_test.py
```

## 🚀 Production Deployment

For production (single server):
1. Build frontend: `cd frontend && pnpm run build`
2. Copy to backend: `cp -r dist/* ../backend/src/static/`
3. Run backend: `cd ../backend && python src/main.py`

The backend will serve both API and frontend on port 5000.

## 📚 Documentation

For detailed information, see the `documentation/` folder:
- Complete setup instructions
- API documentation with examples
- Deployment guides for production
- Technical architecture details
- Business analysis and market research

## 💼 Business Value

- **Target Market**: 57M+ freelancers and small businesses
- **Market Size**: $2.8B legal tech industry  
- **Pricing Strategy**: Freemium model starting at $29/month
- **Competitive Advantage**: 90% cost reduction vs traditional legal review

## 🤝 Support

For help:
1. Check the `documentation/` folder for detailed guides
2. Run the test suite to verify your setup
3. Review the deployment guide for production issues

---

**ContractCritic** - Making contract review accessible, affordable, and intelligent for everyone.

Built with ❤️ using Flask, React, and OpenAI GPT models.


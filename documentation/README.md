# ContractCritic - AI-Powered Contract Review

![ContractCritic Logo](contractcritic_logo.png)

ContractCritic is a comprehensive micro SaaS application that provides AI-powered contract review for freelancers, solopreneurs, and small business owners. Get instant insights, risk assessments, and plain-English explanations of your contracts.

## 🚀 Features

### 🤖 AI-Powered Analysis
- **Smart Contract Review**: Advanced AI analysis using OpenAI GPT models
- **Risk Scoring**: Comprehensive 0-100 risk assessment scale
- **Plain English Summaries**: Complex legal terms explained simply
- **Actionable Recommendations**: Specific suggestions for contract improvements

### 📊 Professional Dashboard
- **Contract Overview**: Visual dashboard with key metrics
- **Risk Distribution**: Color-coded risk level visualization
- **Recent Activity**: Track all contract uploads and analyses
- **Quick Actions**: Streamlined workflow for common tasks

### 📁 File Management
- **Multi-Format Support**: PDF, DOCX, DOC, and TXT files
- **Drag & Drop Upload**: Intuitive file upload interface
- **Secure Storage**: Safe and encrypted file handling
- **Analysis History**: Complete audit trail of all reviews

### 🎨 Modern Interface
- **Responsive Design**: Works perfectly on desktop and mobile
- **Professional UI**: Clean, modern design with Tailwind CSS
- **Intuitive Navigation**: Easy-to-use sidebar and routing
- **Real-time Updates**: Live status updates during analysis

## 🏗️ Architecture

### Backend (Flask)
- **Framework**: Flask with SQLAlchemy ORM
- **Database**: SQLite with comprehensive schema
- **AI Integration**: OpenAI GPT-4 and GPT-3.5 Turbo
- **File Processing**: PyMuPDF (PDF), python-docx (Word)
- **API**: RESTful API with CORS support

### Frontend (React)
- **Framework**: React 18 with Vite
- **UI Library**: Tailwind CSS + shadcn/ui components
- **Routing**: React Router DOM for SPA navigation
- **State Management**: React hooks and context
- **File Upload**: React Dropzone with progress tracking

## 📋 Requirements

- **Python**: 3.11 or higher
- **Node.js**: 20 or higher
- **OpenAI API Key**: Required for contract analysis
- **Storage**: 10GB recommended for file storage
- **Memory**: 2GB RAM minimum

## 🛠️ Installation

### 1. Backend Setup
```bash
cd contractcritic-backend
source venv/bin/activate
pip install -r requirements.txt
export OPENAI_API_KEY=your_openai_api_key_here
python src/main.py
```

### 2. Frontend Setup
```bash
cd contractcritic-frontend
pnpm install
pnpm run dev
```

### 3. Full-Stack Deployment
```bash
# Build frontend
cd contractcritic-frontend
pnpm run build

# Copy to backend
cp -r dist/* ../contractcritic-backend/src/static/

# Deploy backend (includes frontend)
cd ../contractcritic-backend
python src/main.py
```

## 🔧 Configuration

### Environment Variables
```bash
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_API_BASE=https://api.openai.com/v1  # Optional
FLASK_DEBUG=0  # Set to 1 for development
```

### File Upload Limits
- **Maximum file size**: 10MB
- **Supported formats**: PDF, DOCX, DOC, TXT
- **Upload directory**: `src/uploads/`

## 📖 API Documentation

### Core Endpoints

#### Health Check
```http
GET /api/health
```

#### Dashboard Statistics
```http
GET /api/dashboard/stats?user_id={id}
```

#### Contract Management
```http
POST /api/contracts/upload
GET /api/contracts?user_id={id}
GET /api/contracts/{id}
DELETE /api/contracts/{id}
```

#### AI Analysis
```http
POST /api/contracts/{id}/analyze
GET /api/contracts/{id}/analysis
```

## 🎯 Usage

### 1. Upload Contract
- Drag and drop your contract file
- Supported formats: PDF, DOCX, DOC, TXT
- Files are securely processed and stored

### 2. AI Analysis
- Click "Analyze Contract" to start AI review
- Analysis typically takes 10-30 seconds
- Real-time progress updates provided

### 3. Review Results
- **Risk Score**: 0-100 scale with color coding
- **Key Terms**: Important clauses identified
- **Risk Factors**: Specific concerns highlighted
- **Recommendations**: Actionable improvement suggestions
- **Plain English Summary**: Easy-to-understand explanation

### 4. Manage Contracts
- View all contracts in organized list
- Filter by status and search by name
- Track analysis history and results

## 🔒 Security

### File Security
- Secure filename generation
- File type validation
- Size limit enforcement
- Virus scanning recommended for production

### API Security
- Input validation and sanitization
- CORS configuration for cross-origin requests
- Rate limiting recommended for production
- HTTPS enforcement for production deployment

### Data Privacy
- Local file storage (no cloud uploads)
- Encrypted analysis results
- GDPR compliance considerations
- Configurable data retention policies

## 🚀 Deployment Options

### Local Development
- Run backend and frontend separately
- Hot reload for development
- Debug mode with detailed logging

### Production Deployment
- Single Flask app serving both API and frontend
- Optimized build with minification
- Production-ready configuration
- Scalable architecture

### Cloud Deployment
- Compatible with major cloud providers
- Docker containerization ready
- Environment-based configuration
- Auto-scaling capabilities

## 📊 Performance

### AI Analysis
- **GPT-4 Turbo**: Complex contracts, high accuracy
- **GPT-3.5 Turbo**: Simple contracts, fast processing
- **Automatic Model Selection**: Based on content length
- **Cost Optimization**: Intelligent token usage

### File Processing
- **PDF**: Fast text extraction with PyMuPDF
- **Word Documents**: Native python-docx processing
- **Text Files**: Direct processing
- **Concurrent Processing**: Multiple files supported

## 🧪 Testing

### Backend Tests
```bash
cd contractcritic-backend
python simple_test.py
```

### Integration Tests
```bash
python integration_test.py
```

### Frontend Tests
```bash
cd contractcritic-frontend
pnpm run test
```

## 📈 Scaling

### Horizontal Scaling
- Load balancer support
- Database replication ready
- Stateless API design
- CDN integration for assets

### Performance Optimization
- Database indexing
- Caching strategies
- Async processing
- Connection pooling

## 🛠️ Development

### Project Structure
```
contractcritic/
├── contractcritic-backend/          # Flask backend
│   ├── src/
│   │   ├── models/                 # Database models
│   │   ├── routes/                 # API endpoints
│   │   ├── services/               # Business logic
│   │   ├── static/                 # Frontend build files
│   │   └── main.py                 # Application entry point
│   ├── venv/                       # Python virtual environment
│   └── requirements.txt            # Python dependencies
├── contractcritic-frontend/         # React frontend
│   ├── src/
│   │   ├── components/             # React components
│   │   ├── hooks/                  # Custom hooks
│   │   ├── assets/                 # Static assets
│   │   └── App.jsx                 # Main application
│   ├── dist/                       # Build output
│   └── package.json                # Node.js dependencies
└── docs/                           # Documentation
```

### Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Support

For technical support or questions:
- Check the [Deployment Guide](deployment_guide.md)
- Review the [API Documentation](#api-documentation)
- Run the test suite to verify installation
- Contact the development team for assistance

## 🎉 Acknowledgments

- **OpenAI**: For providing the GPT models that power our AI analysis
- **React Team**: For the excellent frontend framework
- **Flask Community**: For the robust backend framework
- **Tailwind CSS**: For the beautiful and responsive design system
- **shadcn/ui**: For the professional UI components

---

**ContractCritic** - Making contract review accessible, affordable, and intelligent for everyone.


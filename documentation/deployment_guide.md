# RuenReview Deployment Guide

## Overview

ContractCritic is a comprehensive micro SaaS application that provides AI-powered contract review for freelancers, solopreneurs, and small business owners. The application consists of a Flask backend with OpenAI integration and a React frontend.

## Architecture

### Backend (Flask)
- **Framework**: Flask with SQLAlchemy
- **Database**: SQLite (production-ready for small to medium scale)
- **AI Integration**: OpenAI GPT models for contract analysis
- **File Processing**: PyMuPDF for PDF, python-docx for Word documents
- **API**: RESTful API with CORS support

### Frontend (React)
- **Framework**: React with Vite
- **UI Library**: Tailwind CSS + shadcn/ui components
- **Routing**: React Router DOM
- **State Management**: React hooks and context
- **File Upload**: React Dropzone with drag-and-drop

## Prerequisites

### Environment Variables
```bash
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_API_BASE=https://api.openai.com/v1  # Optional, defaults to OpenAI
```

### System Requirements
- Python 3.11+
- Node.js 20+
- 2GB RAM minimum
- 10GB storage space

## Local Development Setup

### Backend Setup
```bash
cd contractcritic-backend
source venv/bin/activate
pip install -r requirements.txt
export OPENAI_API_KEY=your_key_here
python src/main.py
```

### Frontend Setup
```bash
cd contractcritic-frontend
pnpm install
pnpm run dev
```

## Production Deployment

### Option 1: Full-Stack Deployment (Recommended)

1. **Build Frontend**
   ```bash
   cd contractcritic-frontend
   pnpm run build
   ```

2. **Copy Frontend to Backend**
   ```bash
   cp -r contractcritic-frontend/dist/* contractcritic-backend/src/static/
   ```

3. **Deploy Backend**
   ```bash
   cd contractcritic-backend
   # Update requirements.txt
   pip freeze > requirements.txt
   ```

### Option 2: Separate Deployments

Deploy backend and frontend separately using the service deployment tools.

## API Endpoints

### Core Endpoints

#### Health Check
- **GET** `/api/health`
- Returns service status and version

#### Dashboard
- **GET** `/api/dashboard/stats?user_id={id}`
- Returns user dashboard statistics

#### Contracts
- **POST** `/api/contracts/upload`
- Upload contract file (PDF, DOCX, DOC, TXT)
- **GET** `/api/contracts?user_id={id}`
- List user contracts with pagination
- **GET** `/api/contracts/{id}`
- Get specific contract details
- **DELETE** `/api/contracts/{id}`
- Delete contract and associated data

#### Analysis
- **POST** `/api/contracts/{id}/analyze`
- Start AI analysis of contract
- **GET** `/api/contracts/{id}/analysis`
- Get latest analysis results
- **GET** `/api/contracts/{id}/analysis/{analysis_id}`
- Get specific analysis by ID

## Features

### Contract Upload
- Drag-and-drop file upload
- Support for PDF, DOCX, DOC, TXT formats
- File size validation (10MB limit)
- Progress tracking and error handling

### AI Analysis
- Comprehensive contract review using OpenAI GPT models
- Risk scoring (0-100 scale)
- Key terms extraction
- Risk factor identification
- Plain English summaries
- Actionable recommendations

### Dashboard
- Contract overview and statistics
- Risk distribution visualization
- Recent activity tracking
- Quick action shortcuts

### Contract Management
- List all contracts with filtering and search
- Status tracking (uploaded, processing, analyzed, error)
- Analysis history and results viewing

## Security Considerations

### File Upload Security
- File type validation
- File size limits
- Secure filename generation
- Virus scanning (recommended for production)

### API Security
- Input validation and sanitization
- Rate limiting (recommended for production)
- Authentication and authorization (to be implemented)
- HTTPS enforcement (production requirement)

### Data Privacy
- Contract files stored locally
- Analysis results encrypted in database
- GDPR compliance considerations
- Data retention policies

## Performance Optimization

### Backend
- Database indexing for frequently queried fields
- Caching for dashboard statistics
- Async processing for long-running analyses
- Connection pooling for database

### Frontend
- Code splitting and lazy loading
- Image optimization
- Bundle size optimization
- CDN for static assets

## Monitoring and Logging

### Application Monitoring
- Health check endpoints
- Performance metrics
- Error tracking and alerting
- Usage analytics

### Logging
- Structured logging with JSON format
- Log levels: DEBUG, INFO, WARNING, ERROR
- Log rotation and retention
- Centralized logging (recommended for production)

## Scaling Considerations

### Horizontal Scaling
- Load balancer configuration
- Session management
- Database replication
- File storage scaling

### Vertical Scaling
- Memory optimization
- CPU utilization monitoring
- Database performance tuning
- Caching strategies

## Backup and Recovery

### Database Backup
- Regular SQLite database backups
- Point-in-time recovery
- Backup verification and testing

### File Storage Backup
- Contract file backup strategy
- Disaster recovery procedures
- Data integrity verification

## Cost Optimization

### OpenAI API Usage
- Model selection based on content length
- Token usage monitoring and optimization
- Cost tracking and budgeting
- Caching of analysis results

### Infrastructure Costs
- Resource utilization monitoring
- Auto-scaling policies
- Reserved instance planning
- Cost allocation and tracking

## Troubleshooting

### Common Issues

#### Backend Issues
- **Database connection errors**: Check SQLite file permissions
- **OpenAI API errors**: Verify API key and quota
- **File upload failures**: Check disk space and permissions

#### Frontend Issues
- **Build failures**: Check Node.js version and dependencies
- **API connection issues**: Verify backend URL configuration
- **UI rendering problems**: Check browser compatibility

### Debug Mode
Enable debug mode for detailed error information:
```bash
export FLASK_DEBUG=1
python src/main.py
```

## Support and Maintenance

### Regular Maintenance Tasks
- Security updates for dependencies
- Database cleanup and optimization
- Log file rotation and cleanup
- Performance monitoring and optimization

### Version Updates
- Semantic versioning strategy
- Database migration procedures
- Backward compatibility considerations
- Rollback procedures

## License and Legal

### Software License
- MIT License (recommended for open source)
- Commercial licensing options
- Third-party license compliance

### Terms of Service
- User agreement templates
- Privacy policy requirements
- Data processing agreements
- Liability limitations

---

For technical support or questions, please refer to the project documentation or contact the development team.


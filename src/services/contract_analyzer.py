import os
import json
import time
import fitz  # PyMuPDF
from docx import Document
from openai import OpenAI
from typing import Dict, List, Optional, Tuple
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ContractAnalyzer:
    def __init__(self):
        self.client = OpenAI(
            api_key=os.getenv('OPENAI_API_KEY'),
            base_url=os.getenv('OPENAI_API_BASE', 'https://api.openai.com/v1')
        )
        
        # Risk scoring weights
        self.risk_weights = {
            'payment_risk': 0.25,
            'liability_risk': 0.20,
            'termination_risk': 0.15,
            'ip_risk': 0.15,
            'compliance_risk': 0.10,
            'clarity_risk': 0.10,
            'enforceability_risk': 0.05
        }
        
        # Model selection thresholds
        self.model_selection = {
            'gpt-4-turbo': {
                'max_tokens': 128000,
                'cost_per_1k_input': 0.01,
                'cost_per_1k_output': 0.03
            },
            'gpt-3.5-turbo': {
                'max_tokens': 16000,
                'cost_per_1k_input': 0.0005,
                'cost_per_1k_output': 0.0015
            }
        }

    def extract_text_from_file(self, file_path: str) -> Dict[str, any]:
        """
        Extract text content from uploaded contract files.
        Supports PDF, DOCX, and TXT formats.
        """
        try:
            file_extension = os.path.splitext(file_path)[1].lower()
            
            if file_extension == '.pdf':
                return self._extract_from_pdf(file_path)
            elif file_extension in ['.docx', '.doc']:
                return self._extract_from_docx(file_path)
            elif file_extension == '.txt':
                return self._extract_from_txt(file_path)
            else:
                raise ValueError(f"Unsupported file format: {file_extension}")
                
        except Exception as e:
            logger.error(f"Error extracting text from {file_path}: {str(e)}")
            raise

    def _extract_from_pdf(self, file_path: str) -> Dict[str, any]:
        """Extract text from PDF using PyMuPDF"""
        document = fitz.open(file_path)
        text_content = []
        
        for page_num in range(len(document)):
            page = document.load_page(page_num)
            text_content.append(page.get_text())
        
        document.close()
        raw_text = "\n".join(text_content)
        
        return {
            'raw_text': raw_text,
            'cleaned_text': self._clean_text(raw_text),
            'page_count': len(text_content),
            'word_count': len(raw_text.split()),
            'char_count': len(raw_text)
        }

    def _extract_from_docx(self, file_path: str) -> Dict[str, any]:
        """Extract text from DOCX using python-docx"""
        doc = Document(file_path)
        text_content = []
        
        for paragraph in doc.paragraphs:
            text_content.append(paragraph.text)
        
        raw_text = "\n".join(text_content)
        
        return {
            'raw_text': raw_text,
            'cleaned_text': self._clean_text(raw_text),
            'page_count': 1,  # DOCX doesn't have clear page breaks
            'word_count': len(raw_text.split()),
            'char_count': len(raw_text)
        }

    def _extract_from_txt(self, file_path: str) -> Dict[str, any]:
        """Extract text from TXT file"""
        with open(file_path, 'r', encoding='utf-8') as file:
            raw_text = file.read()
        
        return {
            'raw_text': raw_text,
            'cleaned_text': self._clean_text(raw_text),
            'page_count': 1,
            'word_count': len(raw_text.split()),
            'char_count': len(raw_text)
        }

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text content"""
        # Remove excessive whitespace
        cleaned = ' '.join(text.split())
        
        # Remove common PDF artifacts
        cleaned = cleaned.replace('\x0c', ' ')  # Form feed
        cleaned = cleaned.replace('\xa0', ' ')  # Non-breaking space
        
        return cleaned

    def select_ai_model(self, text_length: int, analysis_type: str) -> str:
        """
        Select the appropriate AI model based on text length and analysis requirements.
        """
        # Estimate tokens (rough approximation: 1 token ≈ 4 characters)
        estimated_tokens = text_length / 4
        
        if analysis_type == "comprehensive" or estimated_tokens > 15000:
            return "gpt-4-turbo"
        elif analysis_type == "quick_summary" or estimated_tokens < 5000:
            return "gpt-3.5-turbo"
        else:
            return "gpt-4-turbo"  # Default to better model for accuracy

    def analyze_contract(self, contract_text: str, analysis_type: str = "comprehensive") -> Dict[str, any]:
        """
        Perform AI-powered contract analysis using OpenAI GPT models.
        """
        start_time = time.time()
        
        try:
            # Select appropriate model
            model = self.select_ai_model(len(contract_text), analysis_type)
            
            # Prepare the analysis prompt
            prompt = self._get_analysis_prompt(contract_text, analysis_type)
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert legal analyst specializing in contract review for small businesses and freelancers. Provide thorough, accurate analysis with practical recommendations."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,  # Low temperature for consistent, factual responses
                max_tokens=4000
            )
            
            # Parse the response
            analysis_content = response.choices[0].message.content
            
            # Try to parse as JSON, fallback to structured text
            try:
                analysis_results = json.loads(analysis_content)
            except json.JSONDecodeError:
                # If not valid JSON, create structured response
                analysis_results = self._parse_text_response(analysis_content)
            
            # Calculate processing time
            processing_time = int((time.time() - start_time) * 1000)
            
            # Calculate risk score
            risk_score = self._calculate_risk_score(analysis_results)
            
            # Determine risk level
            risk_level = self._get_risk_level(risk_score)
            
            return {
                'analysis_results': analysis_results,
                'risk_score': risk_score,
                'risk_level': risk_level,
                'ai_model_used': model,
                'processing_time_ms': processing_time,
                'tokens_used': response.usage.total_tokens if response.usage else 0
            }
            
        except Exception as e:
            logger.error(f"Error in contract analysis: {str(e)}")
            raise

    def _get_analysis_prompt(self, contract_text: str, analysis_type: str) -> str:
        """
        Generate the appropriate analysis prompt based on analysis type.
        """
        base_prompt = f"""
Analyze the following contract and provide a comprehensive assessment:

CONTRACT TEXT:
{contract_text}

Please provide your analysis in the following JSON structure:

{{
  "contract_type": "string - type of contract (e.g., Service Agreement, NDA, Employment Contract)",
  "parties": {{
    "party_1": "string - first party name and role",
    "party_2": "string - second party name and role"
  }},
  "key_terms": {{
    "payment_terms": "string - payment schedule and amounts",
    "duration": "string - contract duration or term",
    "termination_clauses": "string - how the contract can be terminated",
    "deliverables": "string - what each party must deliver",
    "governing_law": "string - applicable jurisdiction and laws"
  }},
  "risk_assessment": {{
    "overall_risk_level": "string - Low/Medium/High",
    "risk_factors": ["array of specific risk factors identified"],
    "red_flags": ["array of concerning clauses or missing protections"],
    "missing_clauses": ["array of important clauses that should be added"]
  }},
  "recommendations": {{
    "suggested_changes": ["array of recommended modifications"],
    "negotiation_points": ["array of terms that should be negotiated"],
    "priority_actions": ["array of immediate actions to take"]
  }},
  "plain_english_summary": "string - 2-3 paragraph summary in simple language explaining the contract's main points, risks, and recommendations"
}}

Focus on practical concerns for small business owners and freelancers. Highlight potential financial risks, unclear obligations, and missing protections.
"""
        
        if analysis_type == "quick_summary":
            return base_prompt + "\n\nProvide a concise analysis focusing on the most critical risks and key terms."
        
        return base_prompt

    def _parse_text_response(self, response_text: str) -> Dict[str, any]:
        """
        Parse non-JSON response into structured format.
        """
        # Basic fallback structure if JSON parsing fails
        return {
            "contract_type": "Unknown",
            "parties": {
                "party_1": "Not specified",
                "party_2": "Not specified"
            },
            "key_terms": {
                "payment_terms": "Requires manual review",
                "duration": "Requires manual review",
                "termination_clauses": "Requires manual review",
                "deliverables": "Requires manual review",
                "governing_law": "Requires manual review"
            },
            "risk_assessment": {
                "overall_risk_level": "Medium",
                "risk_factors": ["Analysis parsing error - manual review required"],
                "red_flags": [],
                "missing_clauses": []
            },
            "recommendations": {
                "suggested_changes": ["Have a legal professional review this contract"],
                "negotiation_points": [],
                "priority_actions": ["Manual review recommended due to analysis error"]
            },
            "plain_english_summary": f"Analysis completed but response format was unexpected. Raw analysis: {response_text[:500]}..."
        }

    def _calculate_risk_score(self, analysis_results: Dict[str, any]) -> float:
        """
        Calculate overall risk score based on analysis results.
        Returns score from 0-100 (0 = lowest risk, 100 = highest risk).
        """
        try:
            risk_assessment = analysis_results.get('risk_assessment', {})
            overall_risk = risk_assessment.get('overall_risk_level', 'Medium').lower()
            
            # Base score from overall risk level
            base_scores = {
                'low': 25,
                'medium': 50,
                'high': 75
            }
            
            base_score = base_scores.get(overall_risk, 50)
            
            # Adjust based on risk factors and red flags
            risk_factors = len(risk_assessment.get('risk_factors', []))
            red_flags = len(risk_assessment.get('red_flags', []))
            missing_clauses = len(risk_assessment.get('missing_clauses', []))
            
            # Calculate adjustments
            risk_adjustment = min(risk_factors * 3, 15)  # Max 15 points for risk factors
            red_flag_adjustment = min(red_flags * 5, 20)  # Max 20 points for red flags
            missing_clause_adjustment = min(missing_clauses * 2, 10)  # Max 10 points for missing clauses
            
            final_score = base_score + risk_adjustment + red_flag_adjustment + missing_clause_adjustment
            
            # Ensure score is within bounds
            return min(max(final_score, 0), 100)
            
        except Exception as e:
            logger.error(f"Error calculating risk score: {str(e)}")
            return 50.0  # Default medium risk

    def _get_risk_level(self, risk_score: float) -> str:
        """
        Convert numeric risk score to risk level category.
        """
        if risk_score <= 30:
            return "Low"
        elif risk_score <= 70:
            return "Medium"
        else:
            return "High"

    def extract_risk_factors(self, analysis_results: Dict[str, any]) -> List[Dict[str, str]]:
        """
        Extract individual risk factors from analysis results for database storage.
        """
        risk_factors = []
        
        try:
            risk_assessment = analysis_results.get('risk_assessment', {})
            
            # Process risk factors
            for factor in risk_assessment.get('risk_factors', []):
                risk_factors.append({
                    'category': 'Risk Factor',
                    'severity': 'medium',
                    'description': factor,
                    'recommendation': 'Review and consider mitigation strategies'
                })
            
            # Process red flags as high severity
            for red_flag in risk_assessment.get('red_flags', []):
                risk_factors.append({
                    'category': 'Red Flag',
                    'severity': 'high',
                    'description': red_flag,
                    'recommendation': 'Immediate attention required - consider legal consultation'
                })
            
            # Process missing clauses as medium severity
            for missing in risk_assessment.get('missing_clauses', []):
                risk_factors.append({
                    'category': 'Missing Protection',
                    'severity': 'medium',
                    'description': f"Missing clause: {missing}",
                    'recommendation': 'Consider adding this clause for better protection'
                })
                
        except Exception as e:
            logger.error(f"Error extracting risk factors: {str(e)}")
        
        return risk_factors

    def estimate_analysis_cost(self, text_length: int, model: str) -> float:
        """
        Estimate the cost of analyzing a contract with the specified model.
        """
        try:
            model_info = self.model_selection.get(model, self.model_selection['gpt-3.5-turbo'])
            
            # Rough token estimation (1 token ≈ 4 characters)
            input_tokens = text_length / 4
            
            # Estimate output tokens based on analysis complexity
            output_tokens = min(input_tokens * 0.3, 4000)  # Cap at 4K tokens
            
            input_cost = (input_tokens / 1000) * model_info['cost_per_1k_input']
            output_cost = (output_tokens / 1000) * model_info['cost_per_1k_output']
            
            return round(input_cost + output_cost, 4)
            
        except Exception as e:
            logger.error(f"Error estimating cost: {str(e)}")
            return 0.0


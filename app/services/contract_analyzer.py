import os
import json
import json5
import time
import fitz  # PyMuPDF
import re # Import regex module
from docx import Document
from openai import OpenAI
from typing import Dict, List, Optional, Tuple
import logging
import pprint

from app.core.config import settings
from .prompts import SMALL_BUSINESS_ANALYSIS_PROMPT, INDIVIDUAL_PROMPT

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('contract_analysis.log')
    ]
)
logger = logging.getLogger(__name__)

class ContractAnalyzer:
    def __init__(self):
        self.client = OpenAI(
            api_key=settings.openrouter_api_key,
            base_url=settings.openrouter_base_url
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
            'google/gemini-2.5-flash': {
                'max_tokens': 128000, # Placeholder, adjust as per OpenRouter's actual limits
                'cost_per_1m_input': 1.25, # Placeholder
                'cost_per_1m_output': 10.0 # Placeholder
            },
            'google/gemini-2.5-flash-lite': {
                'max_tokens': 16000, # Placeholder, adjust as per OpenRouter's actual limits
                'cost_per_1m_input': 0.30, # Placeholder
                'cost_per_1m_output': 2.50 # Placeholder
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

        logger.info(f"Extracted text from PDF:\n{raw_text}")
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
        
        if analysis_type == "small_business":
            return "google/gemini-2.5-flash"
        elif analysis_type == "individual":
            return "google/gemini-2.5-flash-lite"
        else:
            return "google/gemini-2.5-flash-lite"

    def analyze_contract(self, contract_text: str, analysis_type: str) -> Dict[str, any]:
        """
        Perform AI-powered contract analysis using OpenRouter models.
        """
        start_time = time.time()
        
        try:
            # Select appropriate model
            model = self.select_ai_model(len(contract_text), analysis_type)
            
            # Prepare the analysis prompt
            prompt = self._get_analysis_prompt(contract_text, analysis_type)
            
            # Call OpenRouter API
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert legal analyst specializing in contract review for small businesses, freelancers and individuals. Provide thorough, accurate analysis with practical recommendations."
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
            
            # Log the raw model response
            self._log_model_response(model, analysis_content, response.usage.total_tokens if response.usage else 0)
            
            # Try to parse as JSON, fallback to structured text
            try:
                analysis_results = json.loads(analysis_content)
                logger.info(f"Successfully parsed JSON response from model")
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse JSON from model response, falling back to text parsing")
                # If not valid JSON, create structured response
                analysis_results = self._parse_text_response(analysis_content)
            
            # Calculate processing time
            processing_time = int((time.time() - start_time) * 1000)
            
            # Calculate risk score
            risk_score = self._calculate_risk_score(analysis_results)
            
            # Determine risk level
            risk_level = self._get_risk_level(risk_score)
            
            # Log the analysis results summary
            self._log_analysis_results(analysis_results, risk_score, risk_level)
            
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
        if analysis_type == "small_business":
            return SMALL_BUSINESS_ANALYSIS_PROMPT.format(contract_text=contract_text)
        elif analysis_type == "individual":
            return INDIVIDUAL_PROMPT.format(contract_text=contract_text)
        else:
            raise ValueError("Unknown analysis type")

    def _parse_text_response(self, response_text: str) -> Dict[str, any]:
        """
        Parse non-JSON response into structured format using robust JSON extraction.
        Uses multiple strategies to extract and parse JSON from model responses.
        """
        # Try to extract JSON using multiple regex patterns
        json_patterns = [
            r'\{.*\}',  # Basic JSON object
            r'```json\s*(\{.*?\})\s*```',  # JSON in code blocks
            r'```\s*(\{.*?\})\s*```',  # JSON in generic code blocks
        ]
        
        extracted_json = None
        for pattern in json_patterns:
            match = re.search(pattern, response_text, re.DOTALL)
            if match:
                # Use the first capture group if it exists, otherwise the full match
                json_str = match.group(1) if match.groups() else match.group(0)
                
                # Try standard JSON parsing first
                try:
                    extracted_json = json.loads(json_str)
                    logger.info("Successfully parsed JSON with standard parser")
                    return extracted_json
                except json.JSONDecodeError:
                    pass
                
                # Try json5 parsing for more lenient parsing
                try:
                    extracted_json = json5.loads(json_str)
                    logger.info("Successfully parsed JSON with json5 parser")
                    return extracted_json
                except Exception as e:
                    logger.warning(f"json5 parsing failed: {e}")
                    continue
        
        # If no JSON patterns worked, try to clean and parse the entire response
        cleaned_response = self._clean_json_response(response_text)
        if cleaned_response:
            try:
                extracted_json = json5.loads(cleaned_response)
                logger.info("Successfully parsed cleaned JSON response")
                return extracted_json
            except Exception as e:
                logger.warning(f"Failed to parse cleaned response: {e}")
        
        # Basic fallback structure if no valid JSON is found or parsing fails
        logger.warning("No valid JSON found in response, returning fallback structure.")
        return {
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
            "contract_type": "Unknown",            
            "recommendations": {
                "suggested_changes": ["Have a legal professional review this contract"],
                "negotiation_points": [],
                "priority_actions": ["Manual review recommended due to analysis error"]
            },
            "plain_english_summary": f"Analysis completed but response format was unexpected. Please try again or contact support."
        }

    def _clean_json_response(self, response_text: str) -> str:
        """
        Clean response text to improve JSON parsing success rate.
        """
        # Remove common markdown artifacts
        cleaned = re.sub(r'```json\s*', '', response_text)
        cleaned = re.sub(r'```\s*$', '', cleaned)
        cleaned = re.sub(r'^```\s*', '', cleaned)
        
        # Remove leading/trailing whitespace and newlines
        cleaned = cleaned.strip()
        
        # Try to find the first { and last } to extract just the JSON part
        first_brace = cleaned.find('{')
        last_brace = cleaned.rfind('}')
        
        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            cleaned = cleaned[first_brace:last_brace + 1]
            return cleaned
        
        return None

    def _calculate_risk_score(self, analysis_results: Dict[str, any]) -> float:
        """
        Calculate overall risk score based on analysis results.
        Returns score from 0-100 (0 = lowest risk, 100 = highest risk).
        
        Uses a baseline approach starting with medium-low (25) and adjusting based on
        concrete findings rather than relying heavily on AI's subjective risk assessment.
        """
        try:
            risk_assessment = analysis_results.get('risk_assessment', {})
            
            # Start with a consistent baseline (medium-low)
            base_score = 25
            
            # Get concrete findings from the analysis
            risk_factors = risk_assessment.get('risk_factors', [])
            red_flags = risk_assessment.get('red_flags', [])
            missing_clauses = risk_assessment.get('missing_clauses', [])
            
            # Count the issues
            risk_factor_count = len(risk_factors)
            red_flag_count = len(red_flags)
            missing_clause_count = len(missing_clauses)
            
            # Give more control to the actual findings with higher impact
            risk_adjustment = min(risk_factor_count * 3, 15)     # Max 15 points for risk factors
            red_flag_adjustment = min(red_flag_count * 5, 20)    # Max 20 points for red flags  
            missing_clause_adjustment = min(missing_clause_count * 2, 12)  # Max 12 points for missing clauses

            final_score = base_score + risk_adjustment + red_flag_adjustment + missing_clause_adjustment
            
            # Apply moderate randomization for natural variation
            import random
            random.seed(hash(str(analysis_results)) % 1000)  # Deterministic but varied
            variation = random.uniform(-5, 5)  # Moderate random variation
            final_score += variation
            
            # Add small content-based variation
            content_hash = hash(str(analysis_results.get('key_terms', {}))) % 100
            complexity_adjustment = (content_hash % 6) - 3  # -3 to +2 adjustment
            final_score += complexity_adjustment
            
            # Optional: Small adjustment based on AI's overall assessment (reduced influence)
            overall_risk = risk_assessment.get('overall_risk_level', 'medium').lower()
            overall_risk = overall_risk.replace('_', '-').replace(' ', '-')
            
            ai_adjustment = 0
            if overall_risk == 'low':
                ai_adjustment = -3
            elif overall_risk == 'high':
                ai_adjustment = +3
            # medium, medium-low, medium-high get no adjustment (neutral)
            
            final_score += ai_adjustment
            
            # Ensure score is within bounds
            final_score = min(max(final_score, 0), 100)
            
            # Log the scoring breakdown for debugging
            logger.info(f"Risk scoring breakdown: base={base_score}, risk_factors={risk_adjustment}, "
                       f"red_flags={red_flag_adjustment}, missing={missing_clause_adjustment}, "
                       f"ai_adjustment={ai_adjustment}, variation={variation:.1f}, "
                       f"complexity={complexity_adjustment}, final={final_score:.1f}")
            
            return final_score
            
        except Exception as e:
            logger.error(f"Error calculating risk score: {str(e)}")
            return 25.0  # Default baseline score

    def _get_risk_level(self, risk_score: float) -> str:
        """
        Convert numeric risk score to risk level category.
        Returns a string representing the risk level.
        """
        if risk_score <= 15:
            return "Low"
        elif risk_score <= 35:
            return "Medium-Low"
        elif risk_score <= 65:
            return "Medium"
        elif risk_score <= 85:
            return "Medium-High"
        else:
            return "High"

    def extract_risk_factors(self, analysis_results: Dict[str, any]) -> List[Dict[str, str]]:
        """
        Extract individual risk factors from analysis results for database storage.
        """
        risk_factors = []
        
        try:
            if not analysis_results:
                logger.warning("No analysis results provided to extract_risk_factors")
                return risk_factors
                
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
            model_info = self.model_selection.get(model, self.model_selection['google/gemini-2.5-flash-lite'])

            # Rough token estimation (1 token ≈ 4 characters)
            input_tokens = text_length / 4
            
            # Estimate output tokens based on analysis complexity
            output_tokens = min(input_tokens * 0.3, 4000)  # Cap at 4K tokens
            
            input_cost = (input_tokens / 1000) * model_info['cost_per_1m_input']
            output_cost = (output_tokens / 1000) * model_info['cost_per_1m_output']
            
            return round(input_cost + output_cost, 4)
            
        except Exception as e:
            logger.error(f"Error estimating cost: {str(e)}")
            return 0.0
            
    def _log_model_response(self, model: str, response_content: str, tokens_used: int) -> None:
        """
        Log detailed information about the model response for debugging and analysis.
        """
        logger.info(f"=== MODEL RESPONSE DETAILS ===")
        logger.info(f"Model used: {model}")
        logger.info(f"Tokens used: {tokens_used}")
        
        # Log a preview of the response (first 500 chars)
        preview = response_content[:500] + "..." if len(response_content) > 500 else response_content
        logger.info(f"Response preview: {preview}")
        
        # Log the full response to a separate debug log
        with open('model_responses.log', 'a') as f:
            f.write(f"\n\n=== NEW RESPONSE: {time.strftime('%Y-%m-%d %H:%M:%S')} ===\n")
            f.write(f"Model: {model}\n")
            f.write(f"Tokens: {tokens_used}\n")
            f.write("Full response:\n")
            f.write(response_content)
            f.write("\n=== END RESPONSE ===\n")
        
        logger.info(f"Full response logged to model_responses.log")
    
    def _log_analysis_results(self, analysis_results: Dict[str, any], risk_score: float, risk_level: str) -> None:
        """
        Log a summary of the parsed analysis results.
        """
        logger.info(f"=== ANALYSIS RESULTS SUMMARY ===")
        logger.info(f"Contract type: {analysis_results.get('contract_type', 'Unknown')}")
        logger.info(f"Risk score: {risk_score} ({risk_level})")
        
        # Log key risk factors
        risk_assessment = analysis_results.get('risk_assessment', {})
        risk_factors = risk_assessment.get('risk_factors', [])
        red_flags = risk_assessment.get('red_flags', [])
        
        if risk_factors:
            logger.info(f"Risk factors identified: {len(risk_factors)}")
            for i, factor in enumerate(risk_factors[:3], 1):  # Log first 3 only
                logger.info(f"  {i}. {factor}")
            if len(risk_factors) > 3:
                logger.info(f"  ... and {len(risk_factors) - 3} more")
                
        if red_flags:
            logger.info(f"Red flags identified: {len(red_flags)}")
            for i, flag in enumerate(red_flags[:3], 1):  # Log first 3 only
                logger.info(f"  {i}. {flag}")
            if len(red_flags) > 3:
                logger.info(f"  ... and {len(red_flags) - 3} more")
        
        # Log a more detailed view to a separate file
        with open('analysis_results.log', 'a') as f:
            f.write(f"\n\n=== NEW ANALYSIS: {time.strftime('%Y-%m-%d %H:%M:%S')} ===\n")
            f.write(f"Contract type: {analysis_results.get('contract_type', 'Unknown')}\n")
            f.write(f"Risk score: {risk_score} ({risk_level})\n")
            f.write("Full analysis results:\n")
            f.write(pprint.pformat(analysis_results))
            f.write("\n=== END ANALYSIS ===\n")
            
        logger.info(f"Full analysis results logged to analysis_results.log")

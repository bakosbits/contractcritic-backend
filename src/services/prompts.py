SMALL_BUSINESS_ANALYSIS_PROMPT = """
Analyze the following contract and provide a comprehensive assessment for small businesses and freelancers.

When assessing risk, only assign a higher risk level if the contract contains a high quantity of explicit,
significant red flags. If the contract is standard or lacks clear issues, use a lower risk level.

CONTRACT TEXT:
{contract_text}

Please provide your analysis in the following JSON structure. ENSURE THE ENTIRE RESPONSE IS VALID JSON.

IMPORTANT: Only extract information that is explicitly present in the contract text. If any field is not present, return "Not specified" or null for that field. Do not infer, guess, or make up any information.

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
  "plain_english_key_terms_summary": "string - 1-2 short paragraph summary in simple language explaining the contract's key terms",
  "risk_assessment": {{
    "overall_risk_level": "string - Low/Medium-Low/Medium/Medium-High/High",
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

Respond ONLY with valid JSON. Do not include any extra text, comments, or markdown. If you cannot provide a value, use null.
"""

INDIVIDUAL_PROMPT = """
Analyze the following contract and provide a comprehensive assessment for individuals.

When assessing risk, only assign a higher risk level if the contract contains a high quantity of explicit,
significant red flags. If the contract is standard or lacks clear issues, use a lower risk level.

IMPORTANT: Only extract information that is explicitly present in the contract text. If any field is not present, return "Not specified" or null for that field. Do not infer, guess, or make up any information.

CONTRACT TEXT:
{contract_text}

Please provide your analysis in the following JSON structure. ENSURE THE ENTIRE RESPONSE IS VALID JSON

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
  "plain_english_key_terms_summary": "string - 1-2 short paragraph summary in simple language explaining the contract's key terms",  
  "risk_assessment": {{
    "overall_risk_level": "string - Low/Medium-Low/Medium/Medium-High/High",
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

Focus on practical concerns for individuals. Highlight potential financial risks, unclear obligations, and missing protections.

Respond ONLY with valid JSON. Do not include any extra text, comments, or markdown. If you cannot provide a value, use null.
"""
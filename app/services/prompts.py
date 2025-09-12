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
  "dates": {{
    "execution_date": "string - date contract was signed - no additional text",
    "effective_date": "string - contract effective date - no additional text",
    "expiration_date": "string - contract expiration date - no additional text",
    "termination_date": "string - contract termination date if applicable- no additional text"
  }},
  "risk_assessment": {{
    "overall_risk_level": "string - Low/Medium-Low/Medium/Medium-High/High",
    "risk_factors": ["array of specific risk factors identified"],
    "red_flags": ["array of concerning clauses or missing protections"],
    "missing_clauses": ["array of important clauses that should be added"]
  }}, 
  "risk_guidance": "string - 1 or 2 sentences of guidance on how to best address the identified risk factors",
  "red_flag_guidance": "string - 1 or 2 sentences of guidance on how to best address the identified red flags",
  "missing_clause_guidance": "string - 1 or 2 sentences of guidance on how to best address the identified missing clauses",
  "recommendations": {{
    "suggested_changes": ["array of recommended modifications"],
    "negotiation_points": ["array of terms that should be negotiated"],
    "priority_actions": ["array of immediate actions to take"]
  }},
  "plain_english_summary": "string - 2-3 paragraph summary in simple language explaining the contract's main points, risks, and recommendations"
}}


When extracting dates, only extract the date referenced without any additional text.


--- date examples ---

Correct examples - 
"execution_date": "October 3, 1997",
"effective_date": "October 3, 1997",
"expiration_date": "October 2, 1998",
"termination_date": "October 2, 1998"

Incorrect examples -
"execution_date": "October 3, 1997",
"effective_date": "October 3, 1997",
"expiration_date": "October 2, 1998 (Termination Date)",
"termination_date": "October 2, 1998 (Termination Date)"

--- end date examples ---

Focus on practical concerns for small business owners and freelancers. Highlight potential financial risks, unclear obligations, and missing protections.

Respond ONLY with valid JSON. Do not include any extra text, comments, or markdown. If you cannot provide a value, use null.
"""

INDIVIDUAL_PROMPT = """
Analyze the following contract and provide a comprehensive assessment for individuals.

When assessing risk, only assign a higher risk level if the contract contains a high quantity of explicit,
significant red flags. If the contract is standard or lacks clear issues, use a lower risk level.

IMPORTANT: Only extract information that is explicitly present in the contract text. If any field is not present, return "Not specified" or null for that field. Do not infer, guess, or make up any information.
When extracting dates, only extract the date referenced without any additional text.

Dates example -

correct: 
  "dates": {
    "execution_date": "October 3, 1997",
    "effective_date": "October 3, 1997",
    "expiration_date": "October 2, 1998",
    "termination_date": "October 2, 1998"
  },

incorrect:
  "dates": {
    "execution_date": "October 3, 1997",
    "effective_date": "October 3, 1997",
    "expiration_date": "October 2, 1998 (Termination Date)",
    "termination_date": "October 2, 1998 (Termination Date)"
  },


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
  "dates": {{
    "execution_date": "string - date contract was signed - no additional text",
    "effective_date": "string - contract effective date - no additional text",
    "expiration_date": "string - contract expiration date - no additional text",
    "termination_date": "string - contract termination date if applicable- no additional text"
  }},  
  "risk_assessment": {{
    "overall_risk_level": "string - Low/Medium-Low/Medium/Medium-High/High",
    "risk_factors": ["array of specific risk factors identified"],
    "red_flags": ["array of concerning clauses or missing protections"],
    "missing_clauses": ["array of important clauses that should be added"]
  }}, 
  "risk_guidance": "string - 1 or 2 sentences of guidance on how to best address the identified risk factors",
  "red_flag_guidance": "string - 1 or 2 sentences of guidance on how to best address the identified red flags",
  "missing_clause_guidance": "string - 1 or 2 sentences of guidance on how to best address the identified missing clauses",
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
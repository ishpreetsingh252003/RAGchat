"""
Phase 4: Refusal Template Library

Standardized refusal templates for different violation types and scenarios.
Ensures consistent, compliant responses without PII logging.
"""

from __future__ import annotations

from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum


class RefusalType(Enum):
    """Types of refusal responses."""
    ADVISORY_CONTENT = "advisory_content"
    PII_DETECTED = "pii_detected"
    AMBIGUOUS_QUERY = "ambiguous_query"
    POLICY_VIOLATION = "policy_violation"
    NO_SOURCES = "no_sources"
    INVALID_DOMAIN = "invalid_domain"


@dataclass(frozen=True)
class RefusalTemplate:
    """Standardized refusal template."""
    refusal_type: RefusalType
    title: str
    message: str
    educational_links: List[str]
    severity: str  # "high", "medium", "low"


# Educational links for compliance
EDUCATIONAL_LINKS = {
    "amfi": "https://www.amfiindia.com/investoreducation/understanding-mutual-funds",
    "sebi": "https://www.sebi.gov.in/sebiweb/home/HomeAction.do?doListing=yes&sid=1",
    "risk_disclaimer": "https://www.amfiindia.com/investoreducation/understanding-risk",
    "investor_education": "https://www.rbi.org.in/commonperson/English/Scripts/BS_ViewBS.aspx?Id=1126"
}

# Refusal templates
REFUSAL_TEMPLATES = {
    RefusalType.ADVISORY_CONTENT: RefusalTemplate(
        refusal_type=RefusalType.ADVISORY_CONTENT,
        title="Investment Advice Not Provided",
        message="This assistant provides factual information about mutual funds only and does not give investment advice, recommendations, or suggestions on which funds to buy or sell. For investment guidance, please consult a qualified financial advisor.",
        educational_links=[EDUCATIONAL_LINKS["amfi"], EDUCATIONAL_LINKS["sebi"]],
        severity="high"
    ),
    
    RefusalType.PII_DETECTED: RefusalTemplate(
        refusal_type=RefusalType.PII_DETECTED,
        title="Personal Information Detected",
        message="This assistant does not process or store personal identifiers. Please remove any personal information from your question and ask again using only general, factual wording.",
        educational_links=[EDUCATIONAL_LINKS["investor_education"]],
        severity="high"
    ),
    
    RefusalType.AMBIGUOUS_QUERY: RefusalTemplate(
        refusal_type=RefusalType.AMBIGUOUS_QUERY,
        title="Query Clarification Needed",
        message="I need more specific information to provide a factual answer. Please specify the fund name and the exact information you're looking for (e.g., expense ratio, exit load, minimum SIP amount).",
        educational_links=[EDUCATIONAL_LINKS["amfi"]],
        severity="medium"
    ),
    
    RefusalType.POLICY_VIOLATION: RefusalTemplate(
        refusal_type=RefusalType.POLICY_VIOLATION,
        title="Response Policy Violation",
        message="I apologize, but I cannot provide this response as it doesn't comply with our factual-only guidelines. Please ask a specific question about mutual fund facts.",
        educational_links=[EDUCATIONAL_LINKS["amfi"], EDUCATIONAL_LINKS["risk_disclaimer"]],
        severity="high"
    ),
    
    RefusalType.NO_SOURCES: RefusalTemplate(
        refusal_type=RefusalType.NO_SOURCES,
        title="No Information Available",
        message="I do not find enough information in the curated sources to answer this question. Try rephrasing with a specific scheme name and fact (e.g., exit load, minimum SIP, or benchmark).",
        educational_links=[EDUCATIONAL_LINKS["amfi"]],
        severity="medium"
    ),
    
    RefusalType.INVALID_DOMAIN: RefusalTemplate(
        refusal_type=RefusalType.INVALID_DOMAIN,
        title="Source Validation Error",
        message="I apologize, but I cannot provide information from sources outside our approved list. All answers must come from official mutual fund sources.",
        educational_links=[EDUCATIONAL_LINKS["sebi"], EDUCATIONAL_LINKS["amfi"]],
        severity="high"
    )
}


def get_refusal_template(refusal_type: RefusalType) -> Optional[RefusalTemplate]:
    """Get refusal template by type."""
    return REFUSAL_TEMPLATES.get(refusal_type)


def format_refusal_response(
    refusal_type: RefusalType,
    custom_message: Optional[str] = None,
    additional_context: Optional[Dict[str, str]] = None
) -> Dict[str, any]:
    """
    Format a standardized refusal response.
    
    Args:
        refusal_type: Type of refusal
        custom_message: Optional custom message override
        additional_context: Additional context for personalization
        
    Returns:
        Formatted refusal response dictionary
    """
    template = get_refusal_template(refusal_type)
    if not template:
        # Fallback for unknown refusal types
        template = RefusalTemplate(
            refusal_type=RefusalType.POLICY_VIOLATION,
            title="Unable to Process",
            message="I apologize, but I cannot process this request. Please ask a specific question about mutual fund facts.",
            educational_links=[EDUCATIONAL_LINKS["amfi"]],
            severity="medium"
        )
    
    # Use custom message if provided
    message = custom_message or template.message
    
    # Add context-specific information
    if additional_context:
        for key, value in additional_context.items():
            message = message.replace(f"{{{key}}}", value)
    
    return {
        "grounded": False,
        "refusal_type": refusal_type.value,
        "title": template.title,
        "message": message,
        "educational_links": template.educational_links,
        "severity": template.severity,
        "answer_sentences": [message],
        "citation_url": None,
        "footer": None
    }


def create_advisory_refusal(detected_advice: str) -> Dict[str, any]:
    """Create refusal for advisory content detection."""
    return format_refusal_response(
        RefusalType.ADVISORY_CONTENT,
        additional_context={"detected_advice": detected_advice}
    )


def create_pii_refusal() -> Dict[str, any]:
    """Create refusal for PII detection."""
    return format_refusal_response(RefusalType.PII_DETECTED)


def create_ambiguous_refusal(query_ambiguity: str) -> Dict[str, any]:
    """Create refusal for ambiguous queries."""
    return format_refusal_response(
        RefusalType.AMBIGUOUS_QUERY,
        additional_context={"ambiguity": query_ambiguity}
    )


def create_policy_violation_refusal(violation_types: List[str]) -> Dict[str, any]:
    """Create refusal for policy violations."""
    violations_text = ", ".join(violation_types)
    return format_refusal_response(
        RefusalType.POLICY_VIOLATION,
        custom_message=f"I apologize, but I cannot provide this response due to policy violations: {violations_text}. Please ask a specific question about mutual fund facts."
    )


def create_no_sources_refusal() -> Dict[str, any]:
    """Create refusal for no available sources."""
    return format_refusal_response(RefusalType.NO_SOURCES)


def create_invalid_domain_refusal(invalid_domain: str) -> Dict[str, any]:
    """Create refusal for invalid domain citations."""
    return format_refusal_response(
        RefusalType.INVALID_DOMAIN,
        additional_context={"invalid_domain": invalid_domain}
    )


def get_all_refusal_types() -> List[RefusalType]:
    """Get all available refusal types."""
    return list(RefusalType)


def validate_refusal_response(response: Dict[str, any]) -> bool:
    """Validate that a refusal response is properly formatted."""
    required_fields = ["grounded", "refusal_type", "title", "message", "educational_links"]
    
    for field in required_fields:
        if field not in response:
            return False
    
    # Check that grounded is False for refusals
    if response.get("grounded") is not False:
        return False
    
    # Check that citation_url is None for refusals
    if response.get("citation_url") is not None:
        return False
    
    return True


if __name__ == "__main__":
    # Test refusal templates
    test_cases = [
        ("advisory_content", "Should I invest in HDFC fund?"),
        ("pii_detected", "My PAN is ABCDE1234F, which fund?"),
        ("ambiguous_query", "Tell me about funds"),
        ("policy_violation", ["imperative_buy_sell", "superlative_best"]),
        ("no_sources", "What about XYZ fund?"),
        ("invalid_domain", "https://example.com/fund-info")
    ]
    
    for refusal_type, context in test_cases:
        print(f"Testing {refusal_type}:")
        if refusal_type == "advisory_content":
            response = create_advisory_refusal(context)
        elif refusal_type == "pii_detected":
            response = create_pii_refusal()
        elif refusal_type == "ambiguous_query":
            response = create_ambiguous_refusal(context)
        elif refusal_type == "policy_violation":
            response = create_policy_violation_refusal(context)
        elif refusal_type == "no_sources":
            response = create_no_sources_refusal()
        elif refusal_type == "invalid_domain":
            response = create_invalid_domain_refusal(context)
        
        print(f"  Title: {response['title']}")
        print(f"  Message: {response['message']}")
        print(f"  Valid: {validate_refusal_response(response)}")
        print("-" * 50)

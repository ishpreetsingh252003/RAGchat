"""
Phase 4: Query Router - Refusal Detection and Advisory Classification

Implements classifier + lexicon for routing queries between factual RAG path
and refusal responses based on compliance requirements.
"""

from __future__ import annotations

import re
from typing import Any, Dict, Literal
from dataclasses import dataclass


@dataclass(frozen=True)
class QueryClassification:
    """Classification result with routing decision."""
    path: Literal["refusal", "factual", "ambiguous"]
    reason: str
    confidence: float
    detected_entities: Dict[str, Any]


# Advisory and investment advice keywords
ADVISORY_KEYWORDS = {
    "investment_advice": [
        "should i invest", "should i buy", "should i sell", "should i put",
        "recommend", "recommendation", "advice", "suggest", "suggestion",
        "better fund", "best fund", "which fund", "compare funds",
        "good investment", "bad investment", "worth investing",
        "invest now", "start investing", "stop investing",
        "portfolio", "allocation", "diversify", "rebalance"
    ],
    "performance_queries": [
        "returns", "performance", "profit", "loss", "gain",
        "how much will i get", "expected return", "future value",
        "past performance", "historical returns", "compare returns"
    ],
    "personal_advice": [
        "my situation", "my age", "my income", "my goals",
        "for me", "my risk", "my portfolio", "my investment"
    ]
}

# Factual topic keywords for mutual funds
FACTUAL_KEYWORDS = {
    "fund_details": [
        "expense ratio", "exit load", "entry load", "minimum sip", "sip amount",
        "nav", "net asset value", "aum", "assets under management",
        "fund type", "category", "benchmark", "riskometer", "risk level"
    ],
    "operational": [
        "how to invest", "how to buy", "how to sell", "how to redeem",
        "documents required", "kyc", "pan card", "aadhaar",
        "statement", "account statement", "download statement",
        "customer care", "contact", "helpline"
    ],
    "tax": [
        "tax benefits", "section 80c", "elss", "lock in period",
        "tax saving", "deduction", "capital gains", "tds"
    ]
}


def _contains_advice_indicators(text: str) -> bool:
    """Check if text contains advisory/investment advice indicators."""
    text_lower = text.lower()
    
    for category, keywords in ADVISORY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text_lower:
                return True
    return False


def _contains_factual_indicators(text: str) -> bool:
    """Check if text contains factual mutual fund query indicators."""
    text_lower = text.lower()
    
    for category, keywords in FACTUAL_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text_lower:
                return True
    return False


def _detect_personal_info(text: str) -> bool:
    """Detect if query contains personal information."""
    # Simple patterns for PII detection
    pii_patterns = [
        r'\b\d{10}\b',  # 10-digit numbers (Phone)
        r'\b[A-Z]{5}[0-9]{4}[A-Z]\b', # PAN
        r'\b\d{12}\b',  # 12-digit numbers (Aadhaar)
        r'@.*\.com',  # Email patterns
        r'\b\d{2}/\d{2}/\d{4}\b',  # Date patterns
    ]
    
    for pattern in pii_patterns:
        if re.search(pattern, text, re.I):
            return True
    return False


def _calculate_confidence(advisory_score: int, factual_score: int, pii_score: int) -> float:
    """Calculate classification confidence based on keyword scores."""
    total_score = advisory_score + factual_score + pii_score
    if total_score == 0:
        return 0.5  # Default confidence for ambiguous
    
    # Higher confidence for clear signals
    max_score = max(advisory_score, factual_score, pii_score)
    confidence = max_score / total_score
    return min(confidence, 1.0)


def classify_query(query: str) -> QueryClassification:
    """
    Classify user query for routing decisions.
    
    Returns:
        QueryClassification with path, reason, confidence, and detected entities
    """
    query_clean = query.strip().lower()
    
    # Calculate scores
    advisory_score = 0
    factual_score = 0
    pii_detected = _detect_personal_info(query_clean)
    
    # Count advisory indicators
    for category, keywords in ADVISORY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in query_clean:
                advisory_score += 1
    
    # Count factual indicators  
    for category, keywords in FACTUAL_KEYWORDS.items():
        for keyword in keywords:
            if keyword in query_clean:
                factual_score += 1
    
    # Classification logic
    if pii_detected:
        return QueryClassification(
            path="refusal",
            reason="PII detected in query",
            confidence=1.0,
            detected_entities={"pii": True}
        )
    
    if advisory_score > factual_score and advisory_score > 0:
        return QueryClassification(
            path="refusal", 
            reason=f"Advisory content detected (score: {advisory_score})",
            confidence=_calculate_confidence(advisory_score, factual_score, 0),
            detected_entities={"advisory_score": advisory_score, "factual_score": factual_score}
        )
    
    if factual_score > 0:
        return QueryClassification(
            path="factual",
            reason=f"Factual query detected (score: {factual_score})",
            confidence=_calculate_confidence(advisory_score, factual_score, 0),
            detected_entities={"advisory_score": advisory_score, "factual_score": factual_score}
        )
    
    # Default to ambiguous for unclear queries
    return QueryClassification(
        path="ambiguous",
        reason="Query classification unclear - default to ambiguous",
        confidence=0.3,
        detected_entities={"advisory_score": advisory_score, "factual_score": factual_score}
    )


def route_query(query: str) -> Dict[str, Any]:
    """
    Main routing function for query classification.
    
    Args:
        query: User query string
        
    Returns:
        Dictionary with routing decision and metadata
    """
    classification = classify_query(query)
    
    return {
        "query": query,
        "route": classification.path,
        "reason": classification.reason,
        "confidence": classification.confidence,
        "detected_entities": classification.detected_entities,
        "should_route_to_rag": classification.path == "factual",
        "should_refuse": classification.path in ["refusal", "ambiguous"]
    }


if __name__ == "__main__":
    # Test cases
    test_queries = [
        "Should I invest in HDFC Mid-Cap Fund?",
        "What is the expense ratio of HDFC Equity Fund?",
        "Which fund is better for my retirement?",
        "How to start SIP in HDFC Focused Fund?",
        "My PAN is ABCDE1234F, which fund should I choose?",
        "What is the exit load for HDFC ELSS?",
        "Compare returns of HDFC Large Cap and Mid Cap"
    ]
    
    for query in test_queries:
        result = route_query(query)
        print(f"Query: {query}")
        print(f"Route: {result['route']} (Confidence: {result['confidence']:.2f})")
        print(f"Reason: {result['reason']}")
        print("-" * 50)

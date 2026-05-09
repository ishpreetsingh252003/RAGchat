"""
Phase 4: Response Policy Engine

Validates responses for compliance with refusal handling and constraints.
Blocks outputs containing imperatives, superlatives, and invalid comparisons.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class ViolationType(Enum):
    """Types of policy violations."""
    IMPERATIVE_BUY_SELL = "imperative_buy_sell"
    SUPERLATIVE_BEST = "superlative_best"
    RETURN_COMPARISON = "return_comparison"
    INVALID_DOMAIN = "invalid_domain"
    MULTIPLE_URLS = "multiple_urls"
    NO_CITATION = "no_citation"
    ADVISORY_TONE = "advisory_tone"


@dataclass(frozen=True)
class PolicyViolation:
    """Represents a policy violation."""
    violation_type: ViolationType
    description: str
    severity: str  # "high", "medium", "low"
    position: Optional[str] = None  # Position in text where violation was found


@dataclass(frozen=True)
class PolicyResult:
    """Result of policy validation."""
    is_compliant: bool
    violations: List[PolicyViolation]
    cleaned_text: Optional[str] = None
    recommendation: Optional[str] = None


# Allowed domains for citations
ALLOWED_DOMAINS = {
    "groww.in",
    "hdfcfund.com", 
    "hdfcamc.com",
    "amfiindia.com",
    "sebi.gov.in",
    "rta.amfiindia.com",
    "camsonline.com"
}

# Imperative patterns to block
IMPERATIVE_PATTERNS = [
    r'\b(you should|you must|you need to|invest now|buy now|sell now)\b',
    r'\b(start investing|begin investing|put your money|allocate your)\b',
    r'\b(consider investing|think about investing|we recommend)\b',
    r'\b(best to invest|ideal for|perfect for)\b'
]

# Superlative patterns to block
SUPERLATIVE_PATTERNS = [
    r'\b(best|better|worst|top|perfect|ideal|excellent)\s+fund\b',
    r'\b(highest|lowest|maximum|minimum)\s+(return|gain|performance)\b',
    r'\b(number one|no\.\s*1|first\s+choice)\b',
    r'\b(outperform|underperform|beat|lag)\b'
]

# Return comparison patterns to block
RETURN_COMPARISON_PATTERNS = [
    r'\b(\d+%?\s+(return|gain|profit|loss))\b',
    r'\b(return|gain|profit|loss)\s+of\s+\d+%?\b',
    r'\b(expected|projected|estimated)\s+(return|gain)\b',
    r'\b(will\s+(give|earn|make|return))\b',
    r'\b(compared\s+to|versus|vs\.)\s+\d+%?\b'
]

# Advisory tone patterns
ADVISORY_TONE_PATTERNS = [
    r'\b(we\s+(suggest|recommend|advise|think|believe))\b',
    r'\b(in\s+our\s+opinion|based\s+on\s+analysis)\b',
    r'\b(we\s+(feel|consider|believe)\s+that)\b',
    r'\b(it\s+(would\s+be|might\s+be|could\s+be))\b'
]


def _check_imperatives(text: str) -> List[PolicyViolation]:
    """Check for imperative buy/sell language."""
    violations = []
    
    for pattern in IMPERATIVE_PATTERNS:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            violations.append(PolicyViolation(
                violation_type=ViolationType.IMPERATIVE_BUY_SELL,
                description=f"Imperative language detected: '{match.group()}'",
                severity="high",
                position=f"position {match.start()}-{match.end()}"
            ))
    
    return violations


def _check_superlatives(text: str) -> List[PolicyViolation]:
    """Check for superlative language."""
    violations = []
    
    for pattern in SUPERLATIVE_PATTERNS:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            violations.append(PolicyViolation(
                violation_type=ViolationType.SUPERLATIVE_BEST,
                description=f"Superlative language detected: '{match.group()}'",
                severity="high",
                position=f"position {match.start()}-{match.end()}"
            ))
    
    return violations


def _check_return_comparisons(text: str) -> List[PolicyViolation]:
    """Check for return comparisons not in source text."""
    violations = []
    
    for pattern in RETURN_COMPARISON_PATTERNS:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            violations.append(PolicyViolation(
                violation_type=ViolationType.RETURN_COMPARISON,
                description=f"Return comparison detected: '{match.group()}'",
                severity="high",
                position=f"position {match.start()}-{match.end()}"
            ))
    
    return violations


def _check_advisory_tone(text: str) -> List[PolicyViolation]:
    """Check for advisory tone in responses."""
    violations = []
    
    for pattern in ADVISORY_TONE_PATTERNS:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            violations.append(PolicyViolation(
                violation_type=ViolationType.ADVISORY_TONE,
                description=f"Advisory tone detected: '{match.group()}'",
                severity="medium",
                position=f"position {match.start()}-{match.end()}"
            ))
    
    return violations


def _check_url_compliance(citation_url: Optional[str]) -> List[PolicyViolation]:
    """Check if citation URL is from allowed domain."""
    violations = []
    
    if not citation_url:
        violations.append(PolicyViolation(
            violation_type=ViolationType.NO_CITATION,
            description="No citation URL provided",
            severity="high"
        ))
        return violations
    
    try:
        from urllib.parse import urlparse
        parsed = urlparse(citation_url)
        domain = parsed.netloc.lower()
        
        # Remove www. prefix for comparison
        if domain.startswith('www.'):
            domain = domain[4:]
        
        if domain not in ALLOWED_DOMAINS:
            violations.append(PolicyViolation(
                violation_type=ViolationType.INVALID_DOMAIN,
                description=f"Invalid domain in citation: {domain}",
                severity="high"
            ))
    except Exception:
        violations.append(PolicyViolation(
            violation_type=ViolationType.INVALID_DOMAIN,
            description="Invalid URL format in citation",
            severity="high"
        ))
    
    return violations


def _clean_violations(text: str, violations: List[PolicyViolation]) -> str:
    """Remove or modify text sections with violations."""
    cleaned_text = text
    
    # Sort violations by position (reverse order to maintain indices)
    position_violations = [v for v in violations if v.position is not None]
    position_violations.sort(key=lambda x: int(x.position.split()[1]), reverse=True)
    
    for violation in position_violations:
        if violation.violation_type in [ViolationType.IMPERATIVE_BUY_SELL, ViolationType.SUPERLATIVE_BEST]:
            # Replace with neutral language
            start, end = map(int, violation.position.split()[1::2])
            cleaned_text = cleaned_text[:start] + "[REMOVED: " + violation.description + "]" + cleaned_text[end:]
    
    return cleaned_text


def validate_response(
    answer_sentences: List[str],
    citation_url: Optional[str] = None,
    source_text: Optional[str] = None
) -> PolicyResult:
    """
    Validate response against all policy rules.
    
    Args:
        answer_sentences: List of answer sentences
        citation_url: URL citation (if any)
        source_text: Original source text for comparison
        
    Returns:
        PolicyResult with compliance status and violations
    """
    full_text = " ".join(answer_sentences)
    all_violations = []
    
    # Check all violation types
    all_violations.extend(_check_imperatives(full_text))
    all_violations.extend(_check_superlatives(full_text))
    all_violations.extend(_check_return_comparisons(full_text))
    all_violations.extend(_check_advisory_tone(full_text))
    all_violations.extend(_check_url_compliance(citation_url))
    
    # Determine compliance
    high_severity_violations = [v for v in all_violations if v.severity == "high"]
    is_compliant = len(high_severity_violations) == 0
    
    # Generate recommendation
    recommendation = None
    if not is_compliant:
        if high_severity_violations:
            recommendation = "Response blocked due to policy violations. Please revise to comply with facts-only requirements."
        else:
            recommendation = "Response contains minor policy issues. Consider revising for better compliance."
    
    # Clean text if violations found
    cleaned_text = None
    if all_violations:
        cleaned_text = _clean_violations(full_text, all_violations)
    
    return PolicyResult(
        is_compliant=is_compliant,
        violations=all_violations,
        cleaned_text=cleaned_text,
        recommendation=recommendation
    )


def get_refusal_reason(violations: List[PolicyViolation]) -> str:
    """Get standardized refusal reason from violations."""
    if not violations:
        return "compliant"
    
    high_severity = [v for v in violations if v.severity == "high"]
    if high_severity:
        violation_types = [v.violation_type.value for v in high_severity]
        return f"policy_violation:{','.join(violation_types)}"
    
    medium_severity = [v for v in violations if v.severity == "medium"]
    if medium_severity:
        violation_types = [v.violation_type.value for v in medium_severity]
        return f"policy_warning:{','.join(violation_types)}"
    
    return "compliant"


if __name__ == "__main__":
    # Test cases
    test_responses = [
        {
            "sentences": ["You should invest in HDFC Mid-Cap Fund as it's the best option."],
            "citation": "https://groww.in/mutual-funds/hdfc-mid-cap-fund"
        },
        {
            "sentences": ["The fund has given 15% returns last year."],
            "citation": "https://groww.in/mutual-funds/hdfc-equity-fund"
        },
        {
            "sentences": ["We recommend this fund for long-term goals."],
            "citation": "https://hdfcfund.com"
        },
        {
            "sentences": ["The expense ratio is 2.25% as per factsheet."],
            "citation": "https://hdfcfund.com"
        }
    ]
    
    for i, test in enumerate(test_responses):
        print(f"Test {i+1}: {test['sentences']}")
        result = validate_response(
            answer_sentences=test["sentences"],
            citation_url=test["citation"]
        )
        print(f"Compliant: {result.is_compliant}")
        if result.violations:
            for violation in result.violations:
                print(f"  - {viation.violation_type.value}: {viation.description}")
        print("-" * 50)

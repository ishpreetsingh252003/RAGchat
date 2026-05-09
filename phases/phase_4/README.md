# Phase 4 — Guardrails: Refusal, Advisory Detection, and Safety

**Goals:** Meet **§3 Refusal Handling** and **Constraints** consistently.

## Overview

Phase 4 implements the safety and compliance layer for the Mutual Fund FAQ Assistant. It ensures that all responses comply with the facts-only requirement and prevents investment advice or inappropriate content.

## Components

### 4.1 Query Router (`guardrails/query_router.py`)
- **Purpose**: Classify user queries and route them appropriately
- **Functionality**:
  - Detects advisory/investment advice keywords
  - Identifies factual mutual fund queries
  - Detects PII in user queries
  - Routes to RAG path or triggers refusal
- **Features**:
  - Keyword-based classification with confidence scoring
  - PII detection and protection
  - Support for ambiguous query handling

### 4.2 Response Policy Engine (`guardrails/response_policy.py`)
- **Purpose**: Validate responses against compliance rules
- **Functionality**:
  - Blocks imperative buy/sell language
  - Detects superlatives ("best fund")
  - Prevents return comparisons
  - Validates citation domains
  - Enforces disclaimer-adjacent tone
- **Features**:
  - Pattern-based violation detection
  - Severity classification
  - Text cleaning suggestions

### 4.3 Refusal Template Library (`guardrails/refusal_templates.py`)
- **Purpose**: Standardized refusal responses
- **Functionality**:
  - Consistent refusal messaging
  - Educational resource linking
  - Multiple refusal type support
- **Features**:
  - Template-based responses
  - AMFI/SEBI educational links
  - Customizable messaging

### 4.4 Secure Logger (`guardrails/logger.py`)
- **Purpose**: Track compliance metrics without PII storage
- **Functionality**:
  - PII detection and anonymization
  - Daily log files
  - Metrics tracking
  - Pattern analysis
- **Features**:
  - Zero PII storage policy
  - Daily metrics summaries
  - Refusal pattern analysis

## Usage

### Basic Query Routing
```python
from guardrails.query_router import route_query

result = route_query("Should I invest in HDFC fund?")
if result['should_refuse']:
    # Handle refusal
    pass
else:
    # Route to RAG
    pass
```

### Response Validation
```python
from guardrails.response_policy import validate_response
from guardrails.refusal_templates import create_advisory_refusal

result = validate_response(answer_sentences, citation_url)
if not result.is_compliant:
    # Generate refusal
    refusal = create_advisory_refusal("advisory content")
    return refusal
```

### Logging
```python
from guardrails.logger import log_refusal, log_policy_violation

# Log refusal
log_refusal(
    query="Should I invest?",
    refusal_type="advisory_content",
    reason="Investment advice detected",
    confidence=0.95
)

# Log policy violation
log_policy_violation(
    response_text="This is the best fund",
    violation_types=["superlative_best"],
    severity="high"
)
```

## Compliance Features

### PII Protection
- **Detection**: PAN, Aadhaar, email, phone patterns
- **Anonymization**: Automatic PII removal in logs
- **Zero Storage**: No PII stored in any logs

### Policy Enforcement
- **Imperatives**: Blocks "you should", "invest now", etc.
- **Superlatives**: Blocks "best fund", "top performer", etc.
- **Comparisons**: Blocks return percentage comparisons
- **Domain Validation**: Only allows approved financial domains

### Educational Integration
- **AMFI Links**: Mutual fund education resources
- **SEBI Links**: Regulatory guidance and compliance
- **Risk Disclaimers**: Investment risk education

## Testing

Each component includes test cases demonstrating:
- Query classification accuracy
- Policy violation detection
- Refusal template formatting
- Secure logging functionality

## Integration

Phase 4 integrates between:
- **Input**: User queries from Phase 5 (UI)
- **Output**: Validated responses or refusals to Phase 5 (UI)
- **Side Channel**: Logging for compliance monitoring

## Configuration

The system uses predefined keyword lists and patterns that can be extended:
- Advisory keywords
- Factual keywords  
- PII patterns
- Allowed domains
- Educational resources

## Security Considerations

- **No PII Storage**: Strict policy against personal data
- **Anonymization**: Automatic PII removal
- **Audit Trail**: Complete compliance logging
- **Domain Whitelist**: Only approved financial sources


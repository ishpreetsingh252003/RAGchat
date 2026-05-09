"""
Phase 4: Logging for Refusal Reasons (without PII)

Implements secure logging that captures refusal patterns and metrics
without storing personally identifiable information.
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict


@dataclass(frozen=True)
class LogEntry:
    """Secure log entry without PII."""
    timestamp: str
    log_type: str  # "refusal", "policy_violation", "classification"
    category: str  # refusal_type or violation_type
    reason: str
    query_length: int
    has_pii: bool
    confidence_score: Optional[float] = None
    detected_entities: Optional[Dict[str, Any]] = None
    anonymized_query: Optional[str] = None


class SecureLogger:
    """Logger that prevents PII storage and tracks compliance metrics."""
    
    def __init__(self, log_dir: Optional[Path] = None):
        if log_dir is None:
            log_dir = Path(__file__).parent / "logs"
        
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Daily log files
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        self.log_file = self.log_dir / f"guardrails_{today}.jsonl"
        
        # Metrics tracking
        self.metrics_file = self.log_dir / "metrics.json"
    
    def _anonymize_query(self, query: str) -> str:
        """Remove PII from query for logging."""
        # Remove common PII patterns
        anonymized = query
        
        # Remove PAN patterns (10 characters)
        anonymized = re.sub(r'\b[A-Z]{5}[0-9]{4}[A-Z]\b', '[PAN_REMOVED]', anonymized)
        
        # Remove Aadhaar patterns (12 digits)
        anonymized = re.sub(r'\b\d{12}\b', '[AADHAAR_REMOVED]', anonymized)
        
        # Remove email patterns
        anonymized = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL_REMOVED]', anonymized)
        
        # Remove phone patterns (10 digits)
        anonymized = re.sub(r'\b\d{10}\b', '[PHONE_REMOVED]', anonymized)
        
        # Remove account numbers (6+ digits)
        anonymized = re.sub(r'\b\d{6,}\b', '[ACCOUNT_REMOVED]', anonymized)
        
        return anonymized.strip()
    
    def _detect_pii_in_query(self, query: str) -> bool:
        """Check if query contains PII patterns."""
        pii_patterns = [
            r'\b[A-Z]{5}[0-9]{4}[A-Z]\b',  # PAN
            r'\b\d{12}\b',  # Aadhaar
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email
            r'\b\d{10}\b',  # Phone
            r'\b\d{6,}\b'  # Account numbers
        ]
        
        for pattern in pii_patterns:
            if re.search(pattern, query):
                return True
        return False
    
    def _write_log_entry(self, entry: LogEntry) -> None:
        """Write log entry to daily log file."""
        with self.log_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(entry), ensure_ascii=False) + "\n")
    
    def log_refusal(
        self,
        query: str,
        refusal_type: str,
        reason: str,
        confidence: Optional[float] = None,
        detected_entities: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log a refusal event without PII."""
        has_pii = self._detect_pii_in_query(query)
        anonymized_query = self._anonymize_query(query) if has_pii else None
        
        entry = LogEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            log_type="refusal",
            category=refusal_type,
            reason=reason,
            query_length=len(query),
            has_pii=has_pii,
            confidence_score=confidence,
            detected_entities=detected_entities,
            anonymized_query=anonymized_query
        )
        
        self._write_log_entry(entry)
        self._update_metrics("refusal", refusal_type)
    
    def log_policy_violation(
        self,
        response_text: str,
        violation_types: List[str],
        severity: str
    ) -> None:
        """Log a policy violation event."""
        entry = LogEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            log_type="policy_violation",
            category=",".join(violation_types),
            reason=f"Policy violations detected: {', '.join(violation_types)}",
            query_length=len(response_text),
            has_pii=False,
            confidence_score=None,
            detected_entities={"violation_count": len(violation_types), "severity": severity}
        )
        
        self._write_log_entry(entry)
        self._update_metrics("policy_violation", ",".join(violation_types))
    
    def log_classification(
        self,
        query: str,
        route: str,
        confidence: float,
        detected_entities: Dict[str, Any]
    ) -> None:
        """Log a query classification event."""
        has_pii = self._detect_pii_in_query(query)
        anonymized_query = self._anonymize_query(query) if has_pii else None
        
        entry = LogEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            log_type="classification",
            category=route,
            reason=f"Query routed to {route}",
            query_length=len(query),
            has_pii=has_pii,
            confidence_score=confidence,
            detected_entities=detected_entities,
            anonymized_query=anonymized_query
        )
        
        self._write_log_entry(entry)
        self._update_metrics("classification", route)
    
    def _update_metrics(self, log_type: str, category: str) -> None:
        """Update daily metrics tracking."""
        metrics = self._load_metrics()
        
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        if today not in metrics:
            metrics[today] = {
                "refusals": {},
                "policy_violations": {},
                "classifications": {},
                "total_queries": 0,
                "pii_detected": 0
            }
        
        daily_metrics = metrics[today]
        
        if log_type == "refusal":
            daily_metrics["refusals"][category] = daily_metrics["refusals"].get(category, 0) + 1
        elif log_type == "policy_violation":
            daily_metrics["policy_violations"][category] = daily_metrics["policy_violations"].get(category, 0) + 1
        elif log_type == "classification":
            daily_metrics["classifications"][category] = daily_metrics["classifications"].get(category, 0) + 1
            daily_metrics["total_queries"] += 1
        
        self._save_metrics(metrics)
    
    def _load_metrics(self) -> Dict[str, Any]:
        """Load metrics from file."""
        if not self.metrics_file.exists():
            return {}
        
        try:
            with self.metrics_file.open("r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    
    def _save_metrics(self, metrics: Dict[str, Any]) -> None:
        """Save metrics to file."""
        with self.metrics_file.open("w", encoding="utf-8") as f:
            json.dump(metrics, f, indent=2, ensure_ascii=False)
    
    def get_daily_summary(self, date: Optional[str] = None) -> Dict[str, Any]:
        """Get daily summary statistics."""
        if date is None:
            date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        
        metrics = self._load_metrics()
        return metrics.get(date, {})
    
    def get_refusal_patterns(self, days: int = 7) -> Dict[str, int]:
        """Analyze refusal patterns over recent days."""
        metrics = self._load_metrics()
        patterns = {}
        
        from datetime import timedelta
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)
        
        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.strftime("%Y-%m-%d")
            daily_metrics = metrics.get(date_str, {})
            
            for refusal_type, count in daily_metrics.get("refusals", {}).items():
                patterns[refusal_type] = patterns.get(refusal_type, 0) + count
            
            current_date += timedelta(days=1)
        
        return patterns


# Global logger instance
_logger = None


def get_logger() -> SecureLogger:
    """Get or create the global logger instance."""
    global _logger
    if _logger is None:
        _logger = SecureLogger()
    return _logger


def log_refusal(
    query: str,
    refusal_type: str,
    reason: str,
    confidence: Optional[float] = None,
    detected_entities: Optional[Dict[str, Any]] = None
) -> None:
    """Convenience function to log refusals."""
    logger = get_logger()
    logger.log_refusal(query, refusal_type, reason, confidence, detected_entities)


def log_policy_violation(
    response_text: str,
    violation_types: List[str],
    severity: str
) -> None:
    """Convenience function to log policy violations."""
    logger = get_logger()
    logger.log_policy_violation(response_text, violation_types, severity)


def log_classification(
    query: str,
    route: str,
    confidence: float,
    detected_entities: Dict[str, Any]
) -> None:
    """Convenience function to log classifications."""
    logger = get_logger()
    logger.log_classification(query, route, confidence, detected_entities)


if __name__ == "__main__":
    # Test logging functionality
    logger = SecureLogger()
    
    # Test refusal logging
    logger.log_refusal(
        query="Should I invest in HDFC fund?",
        refusal_type="advisory_content",
        reason="Investment advice detected",
        confidence=0.95,
        detected_entities={"advisory_score": 2}
    )
    
    # Test PII detection
    logger.log_refusal(
        query="My PAN is ABCDE1234F, which fund?",
        refusal_type="pii_detected",
        reason="PII detected in query"
    )
    
    # Test policy violation
    logger.log_policy_violation(
        response_text="This is the best fund for you.",
        violation_types=["superlative_best", "advisory_tone"],
        severity="high"
    )
    
    # Test classification
    logger.log_classification(
        query="What is the expense ratio?",
        route="factual",
        confidence=0.85,
        detected_entities={"factual_score": 2}
    )
    
    print("Logging test completed. Check logs directory for output.")
    print(f"Daily summary: {logger.get_daily_summary()}")

"""
API Main Entry Point - Connects Frontend (Phase 5) with Backend (Phases 2-4)

Implements HTTP API that routes user queries through Phase 4 guardrails,
Phase 2 retrieval, Phase 3 generation, and returns responses to frontend.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Add project root to path for imports
import sys
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

# Import phase components
from phases.phase_4.guardrails.query_router import route_query
from phases.phase_4.guardrails.response_policy import validate_response
from phases.phase_4.guardrails.refusal_templates import (
    create_advisory_refusal, create_pii_refusal, create_ambiguous_refusal,
    create_policy_violation_refusal, create_no_sources_refusal
)
from phases.phase_4.guardrails.logger import log_refusal, log_policy_violation, log_classification
from phases.phase_3.generation.answer import synthesize

# Initialize Flask app
app = Flask(__name__)
# Allow CORS from Vercel preview/production and local dev
_cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")
CORS(app, resources={r"/api/*": {"origins": _cors_origins}})

# Configuration
API_VERSION = "v1"
MAX_QUERY_LENGTH = 500


@app.route('/')
def index():
    """Serve the frontend HTML."""
    return render_template('index.html')


@app.route(f'/api/{API_VERSION}/chat', methods=['POST'])
def chat():
    """
    Main chat endpoint that processes user queries through the full pipeline.
    
    Pipeline: User Query → Phase 4 Router → Phase 2/3 → Phase 4 Policy → Response
    """
    try:
        # Get request data
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({
                "error": "Missing 'query' field in request",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }), 400
        
        query = data['query'].strip()
        
        # Validate query length
        if len(query) > MAX_QUERY_LENGTH:
            return jsonify({
                "error": f"Query too long. Maximum {MAX_QUERY_LENGTH} characters allowed.",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }), 400
        
        # Phase 4: Query Router - Classify and route
        routing_result = route_query(query)
        log_classification(
            query=query,
            route=routing_result['route'],
            confidence=routing_result['confidence'],
            detected_entities=routing_result['detected_entities']
        )
        
        # Handle refusals directly
        if routing_result['should_refuse']:
            if routing_result['route'] == 'refusal':
                refusal_type = routing_result['detected_entities'].get('advisory_score', 0) > 0 and 'advisory_content' or 'policy_violation'
                log_refusal(
                    query=query,
                    refusal_type=refusal_type,
                    reason=routing_result['reason'],
                    confidence=routing_result['confidence']
                )
                
                if refusal_type == 'advisory_content':
                    return jsonify(create_advisory_refusal(routing_result['reason']))
                else:
                    return jsonify(create_policy_violation_refusal(['general_refusal']))
            
            elif routing_result['route'] == 'ambiguous':
                log_refusal(
                    query=query,
                    refusal_type='ambiguous_query',
                    reason=routing_result['reason'],
                    confidence=routing_result['confidence']
                )
                return jsonify(create_ambiguous_refusal(routing_result['reason']))
        
        # Phase 2/3: RAG Pipeline for factual queries
        if routing_result['should_route_to_rag']:
            try:
                # Phase 3: Generate answer using Gemini
                generation_result = synthesize(query, k=3)
                
                # Phase 4: Validate response against policy
                policy_result = validate_response(
                    answer_sentences=generation_result.get('answer_sentences', []),
                    citation_url=generation_result.get('citation_url'),
                    source_text=generation_result.get('retrieval', {}).get('results', [{}])[0].get('text', '') if generation_result.get('retrieval', {}).get('results') else ''
                )
                
                if not policy_result.is_compliant:
                    # Log policy violation
                    violation_types = [v.violation_type.value for v in policy_result.violations]
                    log_policy_violation(
                        response_text=' '.join(generation_result.get('answer_sentences', [])),
                        violation_types=violation_types,
                        severity='high' if any(v.severity == 'high' for v in policy_result.violations) else 'medium'
                    )
                    
                    # Return refusal for policy violation
                    return jsonify(create_policy_violation_refusal(violation_types))
                
                # Return compliant response
                return jsonify({
                    "grounded": generation_result.get('grounded', False),
                    "answer_sentences": generation_result.get('answer_sentences', []),
                    "citation_url": generation_result.get('citation_url'),
                    "footer": generation_result.get('footer'),
                    "retrieval": {
                        "detected": generation_result.get('retrieval', {}).get('detected'),
                        "top_score": generation_result.get('retrieval', {}).get('top_score'),
                        "chunk_id": generation_result.get('retrieval', {}).get('chunk_id')
                    },
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
                
            except Exception as e:
                # Log error and return refusal
                log_refusal(
                    query=query,
                    refusal_type='no_sources',
                    reason=f"Generation error: {str(e)}",
                    confidence=0.0
                )
                return jsonify(create_no_sources_refusal())
        
        # Fallback for unexpected routing
        log_refusal(
            query=query,
            refusal_type='ambiguous_query',
            reason="Unexpected routing result",
            confidence=0.0
        )
        return jsonify(create_ambiguous_refusal("Unable to process request"))
        
    except Exception as e:
        # Global error handling
        return jsonify({
            "error": f"Internal server error: {str(e)}",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }), 500


@app.route(f'/api/{API_VERSION}/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "version": API_VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "components": {
            "phase_4_guardrails": "active",
            "phase_3_generation": "active", 
            "phase_2_retrieval": "active",
            "groq_llm": "configured"
        }
    })


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({
        "error": "Endpoint not found",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    return jsonify({
        "error": "Internal server error",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }), 500


if __name__ == '__main__':
    # Check for required environment variables
    if not os.getenv('GROQ_API_KEY'):
        print("Warning: GROQ_API_KEY environment variable not set")
        print("Phase 3 generation will fail without Groq API key")
    
    # Create templates directory if it doesn't exist
    templates_dir = Path(__file__).parent / 'templates'
    templates_dir.mkdir(exist_ok=True)
    
    # Copy frontend HTML to templates directory
    ui_source = project_root / 'phases' / 'phase_5' / 'ui' / 'index.html'
    ui_target = templates_dir / 'index.html'
    
    if ui_source.exists() and not ui_target.exists():
        import shutil
        shutil.copy2(ui_source, ui_target)
        print(f"Copied frontend to {ui_target}")
    
    port = int(os.getenv("PORT", "5001"))
    print(f"Starting Mutual Fund FAQ Assistant API on port {port}...")
    app.run(host='0.0.0.0', port=port, debug=False)

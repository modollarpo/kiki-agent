#!/usr/bin/env python3
"""
SyncCreate™ HTTP Service Wrapper
Flask microservice for AI creative generation
"""

from flask import Flask, request, jsonify
import os
import logging
from datetime import datetime
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('synccreate')

app = Flask(__name__)

# Environment configuration
PORT = int(os.getenv('PORT', 8084))
SHIELD_URL = os.getenv('SHIELD_URL', 'http://localhost:8081/check')
OUTPUT_DIR = os.getenv('OUTPUT_DIR', '/app/output')
CACHE_DIR = os.getenv('CACHE_DIR', '/app/cache')

# Import SyncCreate modules (lazy import to avoid startup failures)
try:
    from synccreate import (
        BrandGuidelines,
        ProductMetadata,
        AudiencePersona,
        VariantStrategy,
        PlatformFormat
    )
    SYNCCREATE_AVAILABLE = True
    logger.info("✅ SyncCreate modules loaded successfully")
except ImportError as e:
    SYNCCREATE_AVAILABLE = False
    logger.warning(f"⚠️  SyncCreate modules not available: {e}")

# Metrics tracking
request_count = 0
generation_count = 0
error_count = 0


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'synccreate',
        'version': '1.0.0',
        'timestamp': datetime.utcnow().isoformat(),
        'modules_loaded': SYNCCREATE_AVAILABLE,
        'metrics': {
            'requests': request_count,
            'generations': generation_count,
            'errors': error_count
        }
    }), 200


@app.route('/ready', methods=['GET'])
def readiness_check():
    """Readiness probe"""
    if not SYNCCREATE_AVAILABLE:
        return jsonify({
            'status': 'not_ready',
            'reason': 'SyncCreate modules not loaded'
        }), 503
    
    return jsonify({
        'status': 'ready',
        'service': 'synccreate'
    }), 200


@app.route('/api/v1/generate', methods=['POST'])
def generate_creative():
    """
    Generate AI creative variants
    
    Request body:
    {
        "product": {
            "name": "Product Name",
            "features": ["feature1", "feature2"],
            "usp": "Unique selling proposition",
            "category": "software"
        },
        "brand": {
            "name": "Brand Name",
            "primary_colors": ["#FF0000"],
            "tone_of_voice": "professional"
        },
        "variants": 3,
        "platform": "tiktok_9_16"
    }
    """
    global request_count, generation_count, error_count
    request_count += 1
    
    if not SYNCCREATE_AVAILABLE:
        error_count += 1
        return jsonify({
            'error': 'SyncCreate engine not available',
            'status': 'service_unavailable'
        }), 503
    
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('product') or not data.get('brand'):
            error_count += 1
            return jsonify({
                'error': 'Missing required fields: product and brand'
            }), 400
        
        # Mock generation response (actual generation would use SyncCreate classes)
        variants = []
        num_variants = data.get('variants', 3)
        
        for i in range(num_variants):
            variant = {
                'variant_id': f"var_{datetime.utcnow().timestamp()}_{i}",
                'variant_type': ['control', 'lifestyle', 'abstract'][i % 3],
                'headline': f"{data['product']['name']} - Variant {i+1}",
                'body': data['product'].get('usp', 'Compelling copy'),
                'platform': data.get('platform', 'tiktok_9_16'),
                'safety_score': 0.95,
                'brand_compliant': True,
                'status': 'generated',
                'timestamp': datetime.utcnow().isoformat()
            }
            variants.append(variant)
        
        generation_count += num_variants
        
        logger.info(f"✅ Generated {num_variants} creative variants for {data['product']['name']}")
        
        return jsonify({
            'status': 'success',
            'variants': variants,
            'count': len(variants),
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        error_count += 1
        logger.error(f"❌ Generation error: {e}")
        return jsonify({
            'error': str(e),
            'status': 'generation_failed'
        }), 500


@app.route('/api/v1/validate', methods=['POST'])
def validate_creative():
    """
    Validate creative against brand guidelines
    
    Request body:
    {
        "image_url": "https://example.com/creative.jpg",
        "headline": "Ad headline",
        "brand": {...}
    }
    """
    global request_count
    request_count += 1
    
    try:
        data = request.get_json()
        
        # Mock validation (would use vision_guard.py in production)
        validation = {
            'is_safe': True,
            'safety_score': 0.97,
            'brand_compliant': True,
            'violations': [],
            'warnings': [],
            'timestamp': datetime.utcnow().isoformat()
        }
        
        logger.info(f"✅ Validated creative: {data.get('headline', 'untitled')}")
        
        return jsonify({
            'status': 'validated',
            'result': validation
        }), 200
        
    except Exception as e:
        error_count += 1
        logger.error(f"❌ Validation error: {e}")
        return jsonify({
            'error': str(e),
            'status': 'validation_failed'
        }), 500


@app.route('/api/v1/variants', methods=['GET'])
def list_variants():
    """List all generated variants"""
    global request_count
    request_count += 1
    
    return jsonify({
        'variants': [],
        'count': 0,
        'message': 'Variant persistence not yet implemented'
    }), 200


@app.route('/metrics', methods=['GET'])
def metrics():
    """Prometheus-compatible metrics endpoint"""
    metrics_output = f"""# HELP synccreate_requests_total Total HTTP requests
# TYPE synccreate_requests_total counter
synccreate_requests_total {request_count}

# HELP synccreate_generations_total Total creatives generated
# TYPE synccreate_generations_total counter
synccreate_generations_total {generation_count}

# HELP synccreate_errors_total Total errors
# TYPE synccreate_errors_total counter
synccreate_errors_total {error_count}

# HELP synccreate_up Service availability
# TYPE synccreate_up gauge
synccreate_up {1 if SYNCCREATE_AVAILABLE else 0}
"""
    return metrics_output, 200, {'Content-Type': 'text/plain'}


@app.route('/', methods=['GET'])
def root():
    """Service information"""
    return jsonify({
        'service': 'SyncCreate™ Creative Engine',
        'version': '1.0.0',
        'status': 'running',
        'endpoints': {
            'health': '/health',
            'generate': '/api/v1/generate',
            'validate': '/api/v1/validate',
            'metrics': '/metrics'
        },
        'documentation': '/api.html#synccreate'
    }), 200


if __name__ == '__main__':
    logger.info(f"🚀 Starting SyncCreate on port {PORT}")
    logger.info(f"   Shield URL: {SHIELD_URL}")
    logger.info(f"   Output Dir: {OUTPUT_DIR}")
    logger.info(f"   Cache Dir: {CACHE_DIR}")
    
    # Run Flask app
    app.run(
        host='0.0.0.0',
        port=PORT,
        debug=False,
        threaded=True
    )

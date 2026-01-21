"""
SyncCreate™ Interactive Dashboard - Creative Generation UI
Port: 5002 - Enterprise Edition with 5-Variant Strategy
"""

from flask import Flask, render_template_string, request, jsonify
from datetime import datetime
import json
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from cmd.creative.synccreate import (
    SyncCreateEngine,
    BrandSafetyGuardrails,
    AudiencePersona,
    ProductMetadata,
    PlatformFormat,
    BrandGuidelines,
    VariantStrategy
)

app = Flask(__name__)

# Default brand guidelines
DEFAULT_GUIDELINES = BrandGuidelines(
    brand_name="KIKI Agent™",
    primary_colors=["#6366f1", "#8b5cf6", "#ec4899"],
    secondary_colors=["#10b981", "#f59e0b"],
    fonts=["Inter", "SF Pro Display"],
    logo_path="assets/kiki_logo.png",
    tone_of_voice="professional, data-driven, innovative",
    prohibited_terms=["cheap", "spam", "guaranteed", "risk-free", "secret"],
    prohibited_concepts=["violence", "discrimination", "misleading claims"],
    target_audience="B2B SaaS companies and growth teams",
    style_guide="minimalist",
    dei_profile={
        "inclusive_imagery": True,
        "diverse_representation": True,
        "accessible_design": True
    }
)

# Initialize engines
engine = SyncCreateEngine()
safety_guardrails = BrandSafetyGuardrails(DEFAULT_GUIDELINES)

# HTML Template
DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>KIKI SyncCreate™ | AI Creative Generation</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%);
            color: #e2e8f0;
            min-height: 100vh;
            padding: 40px 20px;
        }
        
        .container { max-width: 1400px; margin: 0 auto; }
        
        header {
            text-align: center;
            margin-bottom: 50px;
            border-bottom: 2px solid #475569;
            padding-bottom: 30px;
        }
        
        .logo {
            font-size: 42px;
            font-weight: bold;
            background: linear-gradient(135deg, #ec4899, #8b5cf6, #6366f1);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
        }
        
        .tagline {
            font-size: 16px;
            color: #94a3b8;
            margin-bottom: 20px;
        }
        
        .badge {
            display: inline-block;
            background: rgba(16, 185, 129, 0.2);
            border: 1px solid rgba(16, 185, 129, 0.4);
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 13px;
            font-weight: 600;
            color: #10b981;
        }
        
        .section {
            background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
            border: 1px solid #475569;
            border-radius: 12px;
            padding: 30px;
            margin-bottom: 30px;
        }
        
        h2 {
            font-size: 24px;
            color: #e2e8f0;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #475569;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        label {
            display: block;
            font-size: 13px;
            color: #94a3b8;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 8px;
            font-weight: 600;
        }
        
        input[type="text"], textarea, select {
            width: 100%;
            padding: 12px 16px;
            background: #0f172a;
            border: 1px solid #334155;
            border-radius: 8px;
            color: #e2e8f0;
            font-size: 14px;
            font-family: inherit;
        }
        
        textarea {
            resize: vertical;
            min-height: 100px;
        }
        
        input:focus, textarea:focus, select:focus {
            outline: none;
            border-color: #6366f1;
            box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
        }
        
        .btn {
            padding: 14px 28px;
            border: none;
            border-radius: 8px;
            font-weight: 700;
            font-size: 15px;
            cursor: pointer;
            transition: all 0.3s ease;
            display: inline-flex;
            align-items: center;
            gap: 8px;
        }
        
        .btn-primary {
            background: linear-gradient(135deg, #6366f1, #8b5cf6);
            color: white;
            box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
        }
        
        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(99, 102, 241, 0.4);
        }
        
        .variants-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 24px;
            margin-top: 30px;
        }
        
        .variant-card {
            background: #0f172a;
            border: 1px solid #334155;
            border-radius: 12px;
            padding: 24px;
            transition: all 0.3s ease;
        }
        
        .variant-card:hover {
            transform: translateY(-4px);
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
            border-color: #6366f1;
        }
        
        .variant-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 16px;
        }
        
        .variant-id {
            font-size: 11px;
            color: #64748b;
            font-family: monospace;
        }
        
        .safety-badge {
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
        }
        
        .safety-safe {
            background: rgba(16, 185, 129, 0.2);
            color: #10b981;
        }
        
        .safety-warning {
            background: rgba(245, 158, 11, 0.2);
            color: #f59e0b;
        }
        
        .variant-image {
            width: 100%;
            height: 200px;
            background: linear-gradient(135deg, #1e293b, #0f172a);
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 16px;
            border: 1px solid #334155;
            color: #64748b;
            font-size: 13px;
        }
        
        .variant-headline {
            font-size: 18px;
            font-weight: 700;
            color: #e2e8f0;
            margin-bottom: 12px;
            line-height: 1.3;
        }
        
        .variant-body {
            font-size: 14px;
            color: #cbd5e1;
            margin-bottom: 12px;
            line-height: 1.6;
        }
        
        .variant-cta {
            display: inline-block;
            background: linear-gradient(135deg, #ec4899, #8b5cf6);
            color: white;
            padding: 10px 20px;
            border-radius: 6px;
            font-size: 13px;
            font-weight: 700;
            text-decoration: none;
            margin-bottom: 16px;
        }
        
        .variant-meta {
            border-top: 1px solid #334155;
            padding-top: 12px;
            font-size: 12px;
            color: #64748b;
        }
        
        .meta-item {
            display: flex;
            justify-content: space-between;
            margin-bottom: 6px;
        }
        
        .loading {
            text-align: center;
            padding: 60px 20px;
            color: #94a3b8;
        }
        
        .spinner {
            width: 40px;
            height: 40px;
            border: 4px solid #334155;
            border-top-color: #6366f1;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 0 auto 20px;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        .error {
            background: rgba(239, 68, 68, 0.1);
            border: 1px solid rgba(239, 68, 68, 0.3);
            color: #fca5a5;
            padding: 16px;
            border-radius: 8px;
            margin-top: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div class="logo">🎨 KIKI SyncCreate™</div>
            <div class="tagline">AI Creative Generation with Brand Safety Guardrails</div>
            <span class="badge">✨ Powered by Stable Diffusion</span>
        </header>

        <div class="section">
            <h2>Generate Creative Variants</h2>
            
            <div class="form-group">
                <label>Campaign Concept</label>
                <textarea id="prompt" placeholder="e.g., Marketing automation that drives revenue growth"></textarea>
            </div>
            
            <div class="form-group">
                <label>Brand</label>
                <select id="brand">
                    <option value="kiki">KIKI Agent™ (Default)</option>
                    <option value="custom">Custom Brand</option>
                </select>
            </div>
            
            <div class="form-group">
                <label>Number of Variants</label>
                <select id="variantCount">
                    <option value="2">2 variants (A/B)</option>
                    <option value="3">3 variants (A/B/C)</option>
                    <option value="4" selected>4 variants (A/B/C/D)</option>
                </select>
            </div>
            
            <button class="btn btn-primary" onclick="generateCreatives()">
                ✨ Generate Creatives
            </button>
        </div>

        <div id="results"></div>
    </div>

    <script>
        async function generateCreatives() {
            const prompt = document.getElementById('prompt').value;
            const variantCount = parseInt(document.getElementById('variantCount').value);
            
            if (!prompt.trim()) {
                alert('Please enter a campaign concept');
                return;
            }
            
            const resultsDiv = document.getElementById('results');
            resultsDiv.innerHTML = `
                <div class="section">
                    <div class="loading">
                        <div class="spinner"></div>
                        <p>Generating creative variants with brand safety checks...</p>
                    </div>
                </div>
            `;
            
            try {
                const response = await fetch('/api/creative/generate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        prompt: prompt,
                        variant_count: variantCount,
                        generate_images: true
                    })
                });
                
                const data = await response.json();
                
                if (!response.ok) {
                    throw new Error(data.error || 'Generation failed');
                }
                
                displayVariants(data.variants);
            } catch (error) {
                resultsDiv.innerHTML = `
                    <div class="section">
                        <div class="error">
                            <strong>Error:</strong> ${error.message}
                        </div>
                    </div>
                `;
            }
        }
        
        function displayVariants(variants) {
            const resultsDiv = document.getElementById('results');
            
            let html = `
                <div class="section">
                    <h2>Generated Variants (${variants.length})</h2>
                    <div class="variants-grid">
            `;
            
            variants.forEach((variant, index) => {
                const safetyClass = variant.safety_check.is_safe ? 'safety-safe' : 'safety-warning';
                const safetyLabel = variant.safety_check.is_safe ? '✓ Safe' : '⚠ Review';
                
                html += `
                    <div class="variant-card">
                        <div class="variant-header">
                            <span class="variant-id">Variant ${String.fromCharCode(65 + index)}</span>
                            <span class="safety-badge ${safetyClass}">${safetyLabel}</span>
                        </div>
                        
                        <div class="variant-image">
                            ${variant.image_path ? '🖼️ ' + variant.image_path : '📸 Image Generated'}
                        </div>
                        
                        <div class="variant-headline">${variant.headline}</div>
                        <div class="variant-body">${variant.body_text}</div>
                        <a href="#" class="variant-cta">${variant.cta}</a>
                        
                        <div class="variant-meta">
                            <div class="meta-item">
                                <span>Safety Score:</span>
                                <span>${(variant.safety_check.safety_score * 100).toFixed(0)}%</span>
                            </div>
                            <div class="meta-item">
                                <span>Brand Compliant:</span>
                                <span>${variant.brand_compliance ? '✓ Yes' : '✗ No'}</span>
                            </div>
                            <div class="meta-item">
                                <span>Variant ID:</span>
                                <span style="font-family: monospace; font-size: 10px;">${variant.variant_id}</span>
                            </div>
                        </div>
                    </div>
                `;
            });
            
            html += `
                    </div>
                </div>
            `;
            
            resultsDiv.innerHTML = html;
        }
    </script>
</body>
</html>
"""


@app.route('/')
def index():
    return render_template_string(DASHBOARD_HTML)


@app.route('/api/creative/generate', methods=['POST'])
def api_generate_creative():
    """Generate 5 creative variants with enterprise features."""
    try:
        payload = request.get_json(force=True)
        
        # Build persona from request
        persona_data = payload.get('persona', {})
        persona = AudiencePersona(
            persona_id=f"persona_{persona_data.get('segment_name', 'default').lower().replace(' ', '_')}",
            segment_name=persona_data.get('segment_name', 'Default Segment'),
            ltv_score=float(persona_data.get('ltv_score', 0.75)),
            churn_risk=float(persona_data.get('churn_risk', 0.5)),
            preferred_messaging="results-driven, data-backed",
            pain_points=["ROI uncertainty", "platform complexity"],
            motivations=["efficiency", "competitive advantage"],
            ltv_trigger=persona_data.get('ltv_trigger', 'Standard campaign')
        )
        
        # Build product from request  
        product_data = payload.get('product', {})
        product = ProductMetadata(
            product_name=product_data.get('product_name', 'Product'),
            features=["AI-powered optimization", "Real-time tracking", "Multi-platform management"],
            usp=product_data.get('usp', 'Better results with AI'),
            category=product_data.get('category', 'Technology'),
            visual_assets=["product_dashboard.png"]
        )
        
        # Parse platform format
        platform_map = {
            'tiktok_9_16': PlatformFormat.TIKTOK_VERTICAL,
            'meta_1_1': PlatformFormat.META_SQUARE,
            'linkedin_16_9': PlatformFormat.LINKEDIN_PROFESSIONAL,
            'google_responsive': PlatformFormat.GOOGLE_RESPONSIVE
        }
        platform_format = platform_map.get(payload.get('platform_format', 'meta_1_1'), PlatformFormat.META_SQUARE)
        
        # Generate 5-variant strategy
        variants = engine.generate_creative_variants(
            persona=persona,
            product=product,
            platform_format=platform_format,
            guidelines=DEFAULT_GUIDELINES,
            safety_guardrails=safety_guardrails
        )
        
        # Calculate stats
        variant_count = len(variants)
        avg_safety = sum(v.safety_score for v in variants) / variant_count if variant_count > 0 else 0
        avg_vision = sum(v.vision_validation['quality_score'] for v in variants) / variant_count if variant_count > 0 else 0
        compliance_count = sum(1 for v in variants if v.brand_compliant)
        compliance_rate = (compliance_count / variant_count * 100) if variant_count > 0 else 0
        
        return jsonify({
            'success': True,
            'variants': [
                {
                    'variant_id': v.variant_id,
                    'variant_type': v.variant_type.value,
                    'headline_text': v.headline_text,
                    'body_copy': v.body_copy,
                    'cta_button': v.cta_button,
                    'platform_format': v.platform_format.value,
                    'safety_score': v.safety_score,
                    'brand_compliant': v.brand_compliant,
                    'vision_validation': v.vision_validation,
                    'persona_match': v.persona_match,
                    'sd_prompt': v.sd_prompt[:150] + '...'  # Truncate for display
                }
                for v in variants
            ],
            'stats': {
                'variant_count': variant_count,
                'avg_safety_score': round(avg_safety, 2),
                'avg_vision_quality': round(avg_vision, 2),
                'compliance_rate': int(compliance_rate)
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/brand-guidelines', methods=['GET'])
def api_get_brand_guidelines():
    """Get current brand guidelines."""
    return jsonify({
        'brand_name': DEFAULT_GUIDELINES.brand_name,
        'primary_colors': DEFAULT_GUIDELINES.primary_colors,
        'tone_of_voice': DEFAULT_GUIDELINES.tone_of_voice,
        'style_guide': DEFAULT_GUIDELINES.style_guide,
        'target_audience': DEFAULT_GUIDELINES.target_audience
    })


@app.route('/api/creative/variants/<campaign_name>', methods=['GET'])
def api_get_saved_variants(campaign_name):
    """Retrieve saved creative variants."""
    try:
        variants_file = engine.output_dir / f"{campaign_name}_variants.json"
        if not variants_file.exists():
            return jsonify({'error': 'Campaign not found'}), 404
        
        data = json.loads(variants_file.read_text())
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    print("🎨 Starting SyncCreate™ Dashboard - Enterprise Edition")
    print("🚀 Dashboard URL: http://localhost:5002")
    print("=" * 60)
    print("Features:")
    print("  • 5-Variant Strategy Generation")
    print("  • LTV-Driven Persona Targeting")
    print("  • Three-Gate Safety Check")
    print("  • Platform-Optimized Formats")
    print("  • Real-time Creative Preview")
    print("=" * 60)
    app.run(debug=False, host='0.0.0.0', port=5002)
    
    app.run(host='0.0.0.0', port=5003, debug=True)

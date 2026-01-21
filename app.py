from flask import Flask, send_from_directory
from core.async_value import ltv_bp
from core.sync_value import invoice_bp
from ashield.brand_safety import brand_safety_bp
from core.creative_gallery import creative_gallery_bp

app = Flask(__name__)

# Serve static videos for gallery
@app.route('/static/videos/<path:filename>')
def static_videos(filename):
    return send_from_directory('output/videos', filename)

# Register blueprints
app.register_blueprint(ltv_bp, url_prefix='/api')
app.register_blueprint(invoice_bp, url_prefix='/api')
app.register_blueprint(brand_safety_bp, url_prefix='/api')
app.register_blueprint(creative_gallery_bp, url_prefix='/api')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8085)

from flask import Flask, render_template, jsonify

app = Flask(__name__)

@app.route('/')
def dashboard():
    return '<h1>KIKI Engine Dashboard</h1><p>Welcome to the KIKI Engine running on Bitnami LAMP!</p>'

@app.route('/health')
def health():
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

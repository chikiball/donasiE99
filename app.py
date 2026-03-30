import os
import json
import shutil
from pathlib import Path
from flask import Flask, jsonify, request, send_file

app = Flask(__name__)

# On Fly.io: DATA_DIR=/data (persistent volume)
# Local dev: falls back to ./data or uses ./db.json directly
DATA_DIR  = Path(os.environ.get('DATA_DIR', '/data'))
DB_PATH   = DATA_DIR / 'db.json'
SEED_PATH = Path(__file__).parent / 'db.json'

def ensure_db():
    """On first run, seed /data/db.json from the bundled db.json."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not DB_PATH.exists() and SEED_PATH.exists():
        shutil.copy(SEED_PATH, DB_PATH)

@app.route('/')
def index():
    return send_file('index.html')

@app.route('/api/data')
def get_data():
    ensure_db()
    if DB_PATH.exists():
        return jsonify(json.loads(DB_PATH.read_text(encoding='utf-8')))
    return jsonify({}), 404

@app.route('/api/save', methods=['POST'])
def save_data():
    ensure_db()
    data = request.get_json(force=True)
    if not data:
        return jsonify({'error': 'No data'}), 400
    DB_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding='utf-8'
    )
    return jsonify({'ok': True})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

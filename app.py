from flask import Flask, request, send_file, render_template, jsonify
import os
import subprocess
import tempfile
from api_auth import init_db, generate_api_key, store_api_key, require_api_key
import atexit
import glob
import logging

# 确保模板路径正确
template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'templates'))
app = Flask(__name__, template_folder=template_dir)
TEMP_DIR = tempfile.gettempdir()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 启动时检查模板目录
logger.info(f"Template directory: {template_dir}")
if not os.path.exists(template_dir):
    logger.error(f"Template directory not found: {template_dir}")
else:
    logger.info(f"Template files: {os.listdir(template_dir)}")

# 初始化数据库
init_db()

# 清理临时文件
def cleanup_temp_files():
    pattern = os.path.join(TEMP_DIR, '*.wav')
    for f in glob.glob(pattern):
        try:
            os.remove(f)
        except:
            pass

# 注册退出时的清理函数
atexit.register(cleanup_temp_files)

@app.route('/')
def index():
    try:
        logger.info("Attempting to render index.html")
        return render_template('index.html')
    except Exception as e:
        logger.error(f"Error rendering template: {str(e)}")
        return jsonify({"error": "Template rendering failed"}), 500

@app.route('/api/keys/generate', methods=['POST'])
def generate_key():
    api_key = generate_api_key()
    store_api_key(api_key)
    return jsonify({"api_key": api_key})

@app.route('/api/tts', methods=['POST'])
@require_api_key
def text_to_speech():
    try:
        text = request.form.get('text', '')
        if not text:
            return jsonify({"error": "Text is required"}), 400
            
        lang = request.form.get('lang', 'zh')
        speed = request.form.get('speed', '160')
        pitch = request.form.get('pitch', '50')
        volume = request.form.get('volume', '100')
        voice_variant = request.form.get('voice_variant', '')
        
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            output_file = temp_file.name
        
        cmd = f'espeak-ng -v {lang}{voice_variant} -s {speed} -p {pitch} -a {volume} -w {output_file} "{text}"'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"espeak-ng error: {result.stderr}")
            return jsonify({"error": "Text-to-speech conversion failed"}), 500
            
        return send_file(output_file, mimetype='audio/wav')
        
    except Exception as e:
        logger.error(f"Error in text_to_speech: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

# 定期清理临时文件的路由
@app.route('/api/cleanup', methods=['POST'])
def cleanup():
    cleanup_temp_files()
    return jsonify({"status": "success"})

if __name__ == '__main__':
    logger.info("Starting Flask application...")
    app.run(host='0.0.0.0', port=5000) 

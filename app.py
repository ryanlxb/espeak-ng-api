"""
ESPeak-NG API Service

这是一个基于ESPeak-NG的文字转语音Web服务。
提供REST API和Web界面，支持多语言文本转语音功能。

主要功能：
- Web界面：支持文本输入和参数调整
- REST API：支持程序调用
- 支持多种语言
- 支持语音参数调整（语速、音调、音量等）
"""

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

# 生产环境配置
app.config.update(
    ENV='production',
    DEBUG=False,
    TESTING=False,
    PROPAGATE_EXCEPTIONS=False,
    PRESERVE_CONTEXT_ON_EXCEPTION=None,
    TRAP_HTTP_EXCEPTIONS=False,
    TRAP_BAD_REQUEST_ERRORS=False,
    SECRET_KEY=os.urandom(24),  # 生成随机密钥
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax'
)

TEMP_DIR = tempfile.gettempdir()

# 配置日志系统
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

# 初始化API密钥数据库
init_db()

def cleanup_temp_files():
    """清理临时生成的音频文件"""
    pattern = os.path.join(TEMP_DIR, '*.wav')
    for f in glob.glob(pattern):
        try:
            os.remove(f)
        except:
            pass

# 注册应用退出时的清理函数
atexit.register(cleanup_temp_files)

@app.route('/')
def index():
    """渲染主页面"""
    try:
        logger.info("Attempting to render index.html")
        return render_template('index.html')
    except Exception as e:
        logger.error(f"Error rendering template: {str(e)}")
        return jsonify({"error": "Template rendering failed"}), 500

@app.route('/api/keys/generate', methods=['POST'])
def generate_key():
    """生成新的API密钥"""
    api_key = generate_api_key()
    store_api_key(api_key)
    return jsonify({"api_key": api_key})

@app.route('/api/tts', methods=['POST'])
@require_api_key
def text_to_speech():
    """
    文本转语音API
    
    参数：
    - text: 要转换的文本
    - lang: 语言代码 (默认: zh)
    - speed: 语速 (默认: 160)
    - pitch: 音调 (默认: 50)
    - volume: 音量 (默认: 100)
    - voice_variant: 声音变体
    
    返回：
    - WAV格式的音频文件
    """
    try:
        # 获取并验证参数
        text = request.form.get('text', '')
        if not text:
            return jsonify({"error": "Text is required"}), 400
            
        lang = request.form.get('lang', 'zh')
        speed = request.form.get('speed', '160')
        pitch = request.form.get('pitch', '50')
        volume = request.form.get('volume', '100')
        voice_variant = request.form.get('voice_variant', '')
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            output_file = temp_file.name
        
        # 构建并执行espeak-ng命令
        cmd = f'espeak-ng -v {lang}{voice_variant} -s {speed} -p {pitch} -a {volume} -w {output_file} "{text}"'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        # 检查命令执行结果
        if result.returncode != 0:
            logger.error(f"espeak-ng error: {result.stderr}")
            return jsonify({"error": "Text-to-speech conversion failed"}), 500
            
        return send_file(output_file, mimetype='audio/wav')
        
    except Exception as e:
        logger.error(f"Error in text_to_speech: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/cleanup', methods=['POST'])
def cleanup():
    """手动触发临时文件清理"""
    cleanup_temp_files()
    return jsonify({"status": "success"})

if __name__ == '__main__':
    logger.info("Starting Flask application...")
    app.run(host='0.0.0.0', port=5000) 

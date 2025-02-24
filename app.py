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

def detect_language(text):
    """
    简单的语言检测函数
    """
    # 检查是否包含中文字符
    if any('\u4e00' <= char <= '\u9fff' for char in text):
        return 'zh'
    # 检查是否包含日文字符
    if any('\u3040' <= char <= '\u30ff' for char in text):
        return 'ja'
    # 检查是否包含韩文字符
    if any('\u3130' <= char <= '\u318F' for char in text) or any('\uAC00' <= char <= '\uD7AF' for char in text):
        return 'ko'
    # 默认返回英文
    return 'en'

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
            
        # 检测文本语言
        detected_lang = detect_language(text)
        logger.info(f"检测到的语言: {detected_lang}")
        
        lang = request.form.get('lang', 'zh')
        # 如果检测到的语言与选择的语言不匹配，记录警告
        if detected_lang != lang:
            logger.warning(f"选择的语言({lang})与检测到的语言({detected_lang})不匹配")
        
        # 语言映射
        lang_map = {
            'zh': 'zh-cn',    # 中文（简体）- 使用默认声音
            'en': 'en-us',    # 英文（美国）
            'ja': 'ja',       # 日语
            'ko': 'ko',       # 韩语
        }
        lang = lang_map.get(lang, 'zh-cn')
        
        # 中文目前只支持有限的声音变体
        if lang.startswith('zh'):
            voice_variant = request.form.get('voice_variant', '')
            # 使用正确的语音变体格式
            if voice_variant:
                lang = 'zh-cn' + voice_variant  # 例如：zh-cn+m1
            else:
                lang = 'zh-cn'  # 使用默认声音
        
        speed = request.form.get('speed', '160')
        pitch = request.form.get('pitch', '50')
        volume = request.form.get('volume', '100')
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            output_file = temp_file.name
        
        # 构建并执行espeak-ng命令
        cmd = [
            'espeak-ng',
            '-v', lang,           # 语音/语言
            '-s', str(speed),     # 语速
            '-p', str(pitch),     # 音调
            '-a', str(volume),    # 音量
            '-w', output_file,    # 输出文件
            text                  # 文本内容
        ]
        cmd_str = ' '.join(cmd)
        logger.info(f"执行命令: {cmd_str}")

        # 检查 espeak-ng 是否安装
        check_cmd = "which espeak-ng"
        check_result = subprocess.run(check_cmd, shell=True, capture_output=True, text=True)
        if check_result.returncode != 0:
            logger.error("espeak-ng 未安装或不可访问")
            return jsonify({"error": "espeak-ng not found"}), 500

        # 检查输出目录权限
        if not os.access(os.path.dirname(output_file), os.W_OK):
            logger.error(f"无法写入输出目录: {os.path.dirname(output_file)}")
            return jsonify({"error": "Cannot write to output directory"}), 500

        # 使用列表形式执行命令，避免shell注入和参数解析问题
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )
        logger.info(f"命令执行结果: returncode={result.returncode}")
        logger.info(f"标准输出: {result.stdout}")
        logger.info(f"标准错误: {result.stderr}")
        
        # 检查命令执行结果
        if result.returncode != 0:
            logger.error(f"espeak-ng error: {result.stderr}")
            logger.error(f"espeak-ng output: {result.stdout}")
            return jsonify({"error": "Text-to-speech conversion failed"}), 500
            
        # 检查输出文件是否存在且大小不为0
        if not os.path.exists(output_file) or os.path.getsize(output_file) == 0:
            logger.error(f"输出文件不存在或为空: {output_file}")
            return jsonify({"error": "Output file is empty or not created"}), 500

        logger.info(f"成功生成音频文件: {output_file}, 大小: {os.path.getsize(output_file)} bytes")

        response = send_file(
            output_file,
            mimetype='audio/wav',
            as_attachment=True,
            download_name='tts_output.wav'
        )
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        logger.info("音频文件发送成功")
        return response
        
    except Exception as e:
        logger.error(f"Error in text_to_speech: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/cleanup', methods=['POST'])
def cleanup():
    """手动触发临时文件清理"""
    cleanup_temp_files()
    return jsonify({"status": "success"})

@app.route('/api/languages', methods=['GET'])
def get_available_languages():
    """获取可用的语言列表"""
    try:
        # 执行espeak-ng命令获取支持的语言
        cmd = 'espeak-ng --voices'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"espeak-ng error: {result.stderr}")
            return jsonify({"error": "Failed to get languages"}), 500
            
        # 解析输出获取语言列表
        languages = []
        for line in result.stdout.split('\n'):
            if line.strip():
                parts = line.split()
                if len(parts) >= 4:
                    languages.append({
                        'code': parts[1],
                        'name': ' '.join(parts[3:])
                    })
        
        return jsonify(languages)
        
    except Exception as e:
        logger.error(f"Error in get_available_languages: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    logger.info("Starting Flask application...")
    app.run(host='0.0.0.0', port=5000) 

# ESPeak-NG Web API

基于 ESPeak-NG 的文字转语音 Web 服务，提供 REST API 和 Web 界面。

## 功能特点

- 支持多语言文本转语音
- REST API 接口
- Web 可视化界面
- 可调整语速、音调、音量等参数
- 支持多种男声变体

## 快速开始

### 使用 Docker 运行


## API 使用说明

### 1. 获取 API 密钥

响应示例：

```json
{
    "api_key": "your_generated_api_key"
}
```

### 2. 文本转语音

#### 请求

```bash
curl -X POST http://localhost:5000/api/tts \
  -H "X-API-Key: your_api_key" \
  -F "text=你好世界" \
  -F "lang=zh" \
  -F "speed=160" \
  -F "pitch=50" \
  -F "volume=100" \
  -F "voice_variant=+m1" \
  --output output.wav
```

#### 参数说明

| 参数 | 类型 | 必选 | 说明 | 范围 |
|------|------|------|------|------|
| text | string | 是 | 要转换的文本 | - |
| lang | string | 否 | 语言代码 | zh, en, ja, ko |
| speed | number | 否 | 语速 | 80-500 |
| pitch | number | 否 | 音调 | 0-99 |
| volume | number | 否 | 音量 | 0-200 |
| voice_variant | string | 否 | 声音变体 | +m1, +m2, +m3, +m4 |

#### 语言代码

- zh: 中文（简体）
- en: 英文（美国）
- ja: 日语
- ko: 韩语

### 示例代码

#### Python

```python
import requests

# 获取 API 密钥
response = requests.post('http://localhost:5000/api/keys/generate')
api_key = response.json()['api_key']

# 文本转语音
data = {
    'text': '你好世界',
    'lang': 'zh',
    'speed': '160',
    'pitch': '50',
    'volume': '100',
    'voice_variant': '+m1'
}

headers = {
    'X-API-Key': api_key
}

response = requests.post(
    'http://localhost:5000/api/tts',
    data=data,
    headers=headers
)

# 保存音频文件
if response.status_code == 200:
    with open('output.wav', 'wb') as f:
        f.write(response.content)
```

#### JavaScript

```javascript
// 获取 API 密钥
async function getApiKey() {
    const response = await fetch('http://localhost:5000/api/keys/generate', {
        method: 'POST'
    });
    const data = await response.json();
    return data.api_key;
}

// 文本转语音
async function textToSpeech(apiKey, text) {
    const formData = new FormData();
    formData.append('text', text);
    formData.append('lang', 'zh');
    formData.append('speed', '160');
    formData.append('pitch', '50');
    formData.append('volume', '100');
    formData.append('voice_variant', '+m1');

    const response = await fetch('http://localhost:5000/api/tts', {
        method: 'POST',
        body: formData,
        headers: {
            'X-API-Key': apiKey
        }
    });

    if (response.ok) {
        const blob = await response.blob();
        const audio = new Audio(URL.createObjectURL(blob));
        audio.play();
    }
}

// 使用示例
(async () => {
    const apiKey = await getApiKey();
    await textToSpeech(apiKey, '你好世界');
})();
```

## 错误处理

API 可能返回以下错误：

| 状态码 | 说明 |
|--------|------|
| 400 | 请求参数错误 |
| 401 | API 密钥无效 |
| 500 | 服务器内部错误 |

## 注意事项

1. API 密钥需要在每次请求时通过 `X-API-Key` 请求头传递
2. 音频文件格式为 WAV
3. 中文语音目前仅支持男声变体
4. 建议文本长度不要过长，以避免处理超时

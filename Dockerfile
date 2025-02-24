# 使用Python 3.9精简版作为基础镜像
FROM python:3.9-slim

# 避免在构建过程中出现交互式提示
ENV DEBIAN_FRONTEND=noninteractive

# 安装必要的系统包
# espeak-ng: 文字转语音引擎
# sqlite3: 数据库工具
RUN apt-get update && apt-get install -y \
    espeak-ng \
    espeak-ng-data \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 安装Python依赖
COPY requirements.txt .
RUN pip install -r requirements.txt

# 复制应用文件
COPY . .
RUN chmod -R 755 /app

# 暴露端口
EXPOSE 5000

# 启动应用
CMD ["python", "app.py"] 
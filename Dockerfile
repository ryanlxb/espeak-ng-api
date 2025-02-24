# 使用Python 3.9精简版作为基础镜像
FROM python:3.9-slim

# 避免在构建过程中出现交互式提示
ENV DEBIAN_FRONTEND=noninteractive

# 使用阿里云镜像源
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list && \
    pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/

# 安装必要的系统包
# espeak-ng: 文字转语音引擎
# sqlite3: 数据库工具
RUN apt-get update && apt-get install -y \
    espeak-ng \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 安装Python依赖
COPY requirements.txt .
RUN pip install -r requirements.txt

# 复制所有应用文件到容器中
COPY . .
RUN chmod -R 755 /app

# 创建数据目录并设置权限
RUN mkdir -p /app/data && chmod 777 /app/data

# 设置环境变量
# API密钥数据库路径
ENV SQLITE_DB_PATH=/app/data/api_keys.db
# Flask应用入口
ENV FLASK_APP=app.py
# 运行环境
ENV FLASK_DEBUG=0

# 暴露服务端口
EXPOSE 5000

# 启动应用
CMD ["python", "app.py"] 
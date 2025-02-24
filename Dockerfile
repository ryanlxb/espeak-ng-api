# 使用Python 3.8精简版作为基础镜像
FROM python:3.8-slim

# 避免在构建过程中出现交互式提示
ENV DEBIAN_FRONTEND=noninteractive

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
ENV SQLITE_DB_PATH=/app/data/api_keys.db  # API密钥数据库路径
ENV FLASK_APP=app.py                      # Flask应用入口
ENV FLASK_ENV=production                  # 运行环境

# 暴露服务端口
EXPOSE 5000

# 启动应用
CMD ["python", "app.py"] 
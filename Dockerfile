# 使用Ubuntu作为基础镜像
FROM python:3.8-slim

# 避免交互式提示
ENV DEBIAN_FRONTEND=noninteractive

# 安装必要的包
RUN apt-get update && apt-get install -y \
    espeak-ng \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 安装Python依赖
COPY requirements.txt .
RUN pip install -r requirements.txt

# 复制所有应用文件
COPY . .
RUN chmod -R 755 /app

# 创建数据目录
RUN mkdir -p /app/data && chmod 777 /app/data

# 设置环境变量
ENV SQLITE_DB_PATH=/app/data/api_keys.db
ENV FLASK_APP=app.py
ENV FLASK_ENV=production

# 暴露端口
EXPOSE 5000

# 启动应用
CMD ["python", "app.py"] 
#!/bin/bash

#####################################
# 构建 espeak-ng-api Docker 镜像的脚本
# 
# 功能：
# - 检查必要文件
# - 构建Docker镜像
# - 显示构建结果和使用说明
#####################################

# 镜像配置
IMAGE_NAME="espeak-ng-api"          # Docker镜像名称
IMAGE_TAG="latest"                  # 镜像标签

# 设置Docker镜像源
DOCKER_REGISTRY_MIRRORS=(
    "https://registry.docker-cn.com"
    "https://hub-mirror.c.163.com"
    "https://mirror.baidubce.com"
)

# 测试镜像源连接性并选择最快的
echo "正在测试镜像源连接性..."
for mirror in "${DOCKER_REGISTRY_MIRRORS[@]}"; do
    if curl -s --connect-timeout 3 "$mirror" > /dev/null; then
        echo "使用镜像源: $mirror"
        export DOCKER_REGISTRY_MIRROR="$mirror"
        break
    fi
done

# 开始构建流程
echo "开始构建 ${IMAGE_NAME}:${IMAGE_TAG} 镜像..."

# 检查必要文件是否存在
echo "检查必要文件..."
required_files=("app.py" "api_auth.py" "requirements.txt" "Dockerfile" "templates/index.html")
for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        echo "错误: 找不到必要文件 $file"
        exit 1
    fi
done
echo "文件检查通过"

# 执行Docker构建
echo "开始构建Docker镜像..."
if [ -n "$DOCKER_REGISTRY_MIRROR" ]; then
    docker build --build-arg DOCKER_REGISTRY_MIRROR=$DOCKER_REGISTRY_MIRROR -t ${IMAGE_NAME}:${IMAGE_TAG} .
else
    echo "警告: 未找到可用的镜像源，使用默认源"
    docker build -t ${IMAGE_NAME}:${IMAGE_TAG} .
fi

# 检查构建结果
if [ $? -eq 0 ]; then
    echo "镜像构建成功!"
    echo "镜像信息:"
    docker images ${IMAGE_NAME}:${IMAGE_TAG}  # 显示镜像信息
    
    # 显示使用说明
    echo -e "\n使用以下命令运行容器:"
    echo "docker run -p 5000:5000 ${IMAGE_NAME}:${IMAGE_TAG}"
else
    echo "错误: 镜像构建失败"
    exit 1
fi 
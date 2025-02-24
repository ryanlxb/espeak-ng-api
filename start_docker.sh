#!/bin/bash

#####################################
# 启动 espeak-ng-api Docker 容器的脚本
# 
# 功能：
# - 自动处理已存在的容器
# - 启动新容器
# - 设置自动重启策略
# - 显示服务状态和访问信息
#####################################

# 容器和镜像配置
IMAGE_NAME="espeak-ng-api"          # Docker镜像名称
IMAGE_TAG="latest"                  # 镜像标签
CONTAINER_NAME="espeak-ng-api"      # 容器名称
HOST_PORT=5000                      # 主机端口
CONTAINER_PORT=5000                 # 容器内部端口

# 清理已存在的同名容器（如果存在）
if [ "$(docker ps -q -f name=${CONTAINER_NAME})" ]; then
    echo "警告: 已有同名容器在运行"
    echo "正在停止并删除旧容器..."
    docker stop ${CONTAINER_NAME}    # 停止运行中的容器
    docker rm ${CONTAINER_NAME}      # 删除容器
fi

# 清理已停止的同名容器
if [ "$(docker ps -aq -f status=exited -f name=${CONTAINER_NAME})" ]; then
    echo "发现停止的同名容器，正在删除..."
    docker rm ${CONTAINER_NAME}      # 删除已停止的容器
fi

# 验证镜像是否存在
if [[ "$(docker images -q ${IMAGE_NAME}:${IMAGE_TAG} 2> /dev/null)" == "" ]]; then
    echo "错误: 找不到镜像 ${IMAGE_NAME}:${IMAGE_TAG}"
    echo "请先运行 ./docker_build.sh 构建镜像"
    exit 1
fi

# 启动新容器
echo "正在启动容器..."
docker run -d \                      # 后台运行容器
    --name ${CONTAINER_NAME} \       # 设置容器名称
    -p ${HOST_PORT}:${CONTAINER_PORT} \  # 端口映射
    --restart unless-stopped \       # 自动重启策略
    ${IMAGE_NAME}:${IMAGE_TAG}      # 使用的镜像

# 检查容器启动状态
if [ $? -eq 0 ]; then
    echo "容器启动成功!"
    echo "容器信息:"
    docker ps -f name=${CONTAINER_NAME}  # 显示容器状态
    
    # 显示访问信息
    echo -e "\n服务访问地址:"
    echo "http://localhost:${HOST_PORT}"
    
    # 显示日志查看命令
    echo -e "\n查看日志:"
    echo "docker logs -f ${CONTAINER_NAME}"
else
    echo "错误: 容器启动失败"
    exit 1
fi 
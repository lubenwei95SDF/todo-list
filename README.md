# 📝 Todo List System (V3.1) - 生产级全栈容器化部署

基于 Python Flask 的待办事项管理系统。从 V1.0 单体应用演进至 **V3.1 微服务架构**，实现了全链路容器化、自动化运维及 HTTPS 安全加固。

---

## 🏗️ 系统架构 (Architecture)

```mermaid
graph LR
    User((用户)) -- HTTPS/443 --> Nginx[Nginx 网关]
    Nginx -- 内部网络:8000 --> Web[Flask 后端]
    Web <--> DB[(SQLite 数据库)]
    Cron[Cron 任务容器] -- 每日检查 DDL --> Web

    Nginx: 反向代理网关，负责 SSL 卸载、静态资源转发及端口隐藏。

    Flask (Gunicorn): 核心 RESTful API 服务，无状态设计。

    Cron: 独立容器，负责定时执行邮件提醒任务，与业务逻辑解耦。

✨ 核心特性

    ✅ RESTful API: 标准 CRUD 接口设计。

    ✅ 生产级安全: 强制 HTTPS (TLS 1.2+)，后端端口对公网封闭。

    ✅ 前后端分离: 原生 JS (Fetch API) 实现，无刷新交互。

    ✅ DevOps: Docker Compose 一键编排，解决环境一致性问题。

🚀 快速开始 (Quick Start)
1. 克隆项目
Bash

git clone [https://github.com/yourname/todo-list.git](https://github.com/yourname/todo-list.git)
cd todo-list

2. 生成 SSL 证书 (必需)

本项目启用 HTTPS，需在本地生成自签名证书（证书文件已被 .gitignore 忽略）：
Bash

mkdir -p nginx/ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout nginx/ssl/nginx.key \
    -out nginx/ssl/nginx.crt \
    -subj "/C=CN/ST=Beijing/L=Beijing/O=Dev/CN=localhost"

3. 启动服务
Bash

# 构建镜像并后台运行
sudo docker-compose up -d --build

访问 https://你的服务器IP 即可。 (注：因使用自签名证书，浏览器会提示不安全，请点击“继续访问”)
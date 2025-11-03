# 📅 DDL 待办事项提醒器 (Task Manager)

这是一个基于 Python + Flask + Docker 开发的轻量级个人待办事项（Todo List）Web 应用。

本项目的核心目的是解决个人忘记任务 DDL（截止日期）的痛点。它最大的特色是集成了一个**自动化的后台脚本**，该脚本每天会定时运行，检查所有即将到期的任务，并**发送一封“每日简报”邮件**来提醒用户。

本项目也是一个完整的“全栈”入门实践，涵盖了从“需求分析”、“蓝图设计”到“Web 开发”、“后台脚本”最后到“**Docker 容器化部署**”的全流程。

## ✨ 核心功能

  * **[安全]** **身份认证：** 使用 `Flask Session` + `主密码` 保护整个网站，确保只有自己能访问。
  * **[Web]** **任务管理 (CRUD)：**
      * **创建 (Create):** 添加新任务，并可选地设置 DDL 日期。
      * **读取 (Read):** 在首页清晰地展示所有“未完成”的任务，并按 DDL 排序。
      * **更新 (Update):** 一键将任务标记为“已完成”。
      * **删除 (Delete):** 彻底删除不需要的任务。
  * **[自动化]** **每日邮件简报：**
      * 一个独立的 `Python` 脚本 (`check_ddl.py`)。
      * 由 `Cron` (在 Docker 中) 驱动，每天凌晨 1:00 自动运行。
      * **智能查询：** 找出所有 7 天内（可配置）到期且未完成的任务。
      * **汇总发送：** 将所有到期任务**汇总到一封**邮件中发送，避免邮件风暴。
      * **简洁设计：** 采用“无状态”设计，无需“旗标”，逻辑简单且健壮。

## 🔧 技术栈 (Tech Stack)

本项目所使用的核心技术：

  * **后端 (Backend):** `Python 3.11`, `Flask`
  * **数据库 (Database):** `SQLite`, `Flask-SQLAlchemy` (ORM)
  * **前端 (Frontend):** `HTML5`, `CSS3`, `Jinja2` (模板引擎)
  * **身份认证 (Auth):** `Flask Session` (基于 Cookie)
  * **后台任务 (Automation):** `smtplib` (邮件), `ssl` (安全连接)
  * **Web 服务器 (WSGI):** `Gunicorn` (生产环境服务器)
  * **部署 (DevOps):** `Docker`, `Docker Compose`
  * **定时任务 (Scheduling):** `Cron`

## 🚀 如何运行 (本地部署)

本项目已完全“**容器化**”，部署极其简单。

**前提条件：** 你的电脑上必须安装 `Docker` 和 `Docker Desktop`。

1.  **克隆 (Clone) 本仓库**



2.  **创建“机密”配置文件**
    本项目使用 `config.py` 来管理密码，该文件**不**应上传到 Git。

      * 在根目录**手动**创建一个 `config.py` 文件。
      * **复制**以下内容到 `config.py` 中，并**改成你自己的信息**：

    <!-- end list -->

    ```python
    # config.py

    # --- 1. Flask 安全配置 ---
    # (必须设置！请随便打一串很长很乱的字符)
    SECRET_KEY = 'a-very-long-and-random-string-12345!'

    # (这是你的网站登录密码)
    MASTER_PASSWORD = 'MySuperSecretPassword123' 

    # --- 2. 邮件配置 (以 QQ 邮箱为例) ---
    SMTP_SERVER = 'smtp.qq.com'
    SMTP_PORT = 465 # SSL 端口

    # 你的邮箱账号
    EMAIL_ADDRESS = '123456@qq.com'

    # 你的“应用专用密码”(授权码) - 不是登录密码！
    EMAIL_PASSWORD = 'xxxxxxxxxxxxxxxx' 

    # 接收邮件的地址 (可以和发送地址一样)
    RECIPIENT_EMAIL = '123456@qq.com'
    ```

3.  **构建并启动 Docker 容器**
    在项目根目录（`docker-compose.yml` 所在的目录）运行：

    ```bash
    # (可选) 如果你修改了 Dockerfile，或者第一次构建
    docker-compose build

    # 启动所有服务 (web 和 cron) 在后台运行
    docker-compose up -d
    ```

4.  **（仅限首次运行）初始化数据库**
    应用已在运行，但数据库还是空的。我们需要“进入”容器来创建数据库表。

      * **打开一个新的终端**。
      * 运行 `docker-compose exec` 命令来进入 `web` 容器的 `flask shell`：
        ```bash
        docker-compose exec web flask shell
        ```
      * 你会看到一个 Python 提示符 `>>>`。
      * **输入以下命令**来创建数据库表：
        ```python
        db.create_all()
        ```
      * 创建成功后，输入 `exit()` 退出 `shell`。

5.  **🎉 访问你的应用！**

      * 打开你的浏览器，访问： **`http://127.0.0.1:5000/`**
      * 你会被导向到登录页面。输入你在 `config.py` 中设置的 `MASTER_PASSWORD` 即可开始使用！




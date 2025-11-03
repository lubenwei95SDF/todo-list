import smtplib
import ssl
from email.message import EmailMessage
import config
from datetime import datetime,timedelta
from app import app, db, Task
REMINDER_WINDOW_DAYS = 7



def send_email_brief(email_body_content):
    addr_from = config.EMAIL_ADDRESS
    addr_to = config.RECIPIENT_EMAIL
    password = config.EMAIL_PASSWORD
    smtp_server = config.SMTP_SERVER
    smtp_port = config.SMTP_PORT
    try:
        msg = EmailMessage()
        msg['Subject'] = f"📅 你的 DDL 每日简报({datetime.now().strftime('%Y-%m-%d')})"
        msg['From'] = addr_from
        msg['To'] = addr_to
        msg.set_content(email_body_content, charset = 'utf-8')
        context = ssl.create_default_context()

        print(f"[Email]  正在连接到 {smtp_server}...")
        server = smtplib.SMTP_SSL(smtp_server, smtp_port, context=context)
        server.login(addr_from, password)
        print(f"[Email] 登录成功... 正在发送邮件至 {addr_to}...")
        server.send_message(msg)
        print(f"[Email]邮件发送成功 ！")
        return True
    except Exception as e:
        print(f"[Email ERROR] 邮件发送失败:{e} ")
        return False
    finally:
        if server:
            try:
                server.quit()
                print("[Email] 连接已关闭")
            except Exception as e_quit:
                print(f"[Email WARN] 关闭连接时出错 (可忽略): {e_quit}")
def check_and_notify_daily_brief():
    print(f"---[每日简报检查开始于:{datetime.now()}]---")

    with app.app_context():
        today = datetime.utcnow().date()

        window_end_date = today + timedelta(days = REMINDER_WINDOW_DAYS)

        tasks_to_notify = Task.query.filter(
            Task.is_completed == False,
            Task.due_date >= today,
            Task.due_date <= window_end_date,
        ).order_by(Task.due_date).all()

        if tasks_to_notify:
            print(f"[INFO 找到了 {len(tasks_to_notify)} 个即将到期的任务")
            email_body =  "你好！ \n\n以下是您即将到期的DDL 任务简报： \n\n"
            for task in tasks_to_notify:
                days_left = (task.due_date - today).days
                print(f" - > [ID: {task.id}] {task.title} (剩余{days_left})天")
                email_body += f" - [剩余{days_left} 天] {task.title} (DDL: {task.due_date})\n"
                email_body += "\n请尽快处理。\n"
                print("\n[INFO](模拟) 每日简报邮件已生成。")
            send_email_brief(email_body)
        else :
            print("[INFO] 太棒了！7天内没有即将到期的DDL任务。")
        print(f"--- [每日简报检查结束] ---")

if __name__ == '__main__':
    check_and_notify_daily_brief()
import pika
import json
import time
import os
import sys
RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'localhost')
credentials = pika.PlainCredentials('admin', 'secret')

def connect_mq():
    """
        带重试机制的连接函数
        就像网卡驱动：如果硬件没响应，就轮询等待，而不是直接蓝屏。
        """
    retry_count = 0
    while True:
        try:
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=RABBITMQ_HOST, credentials=credentials)
            )
            print("✅ [Worker] 成功连接到 RabbitMQ!")
            return connection
        except pika.exceptions.AMQPConnectionError as e:
            retry_count += 1
            print(f"⏳ [Worker] 连接 RabbitMQ 失败 (第 {retry_count} 次尝试). 等待 5 秒...")
            time.sleep(5)
        except Exception as e:
            # 如果是其他严重错误（比如解析不了 host），则打印并退出
            print(f"❌ [Worker] 发生严重错误: {e}")
            sys.exit(1)

def send_email_simulation(user_name):
    """
    模拟邮件发送操作
    在单线程Web Server中， 这个操作会卡死用户
    但在 Wokrer中 随便卡
    :param user_name:
    :return:
    """
    print(f"📧 [Worker] 正在为 {user_name} 准备欢迎邮件...")
    time.sleep(5)
    print(f"✅ [Worker] 邮件已发送给 {user_name}!")


def callback(ch, method, properties, body):
    """
    中断处理函数 (Interrupt Handler)
    当队列中有消息时，会自动触发这个函数
    :param ch:
    :param method:
    :param properties:
    :param body:
    :return:
    """
    data = json.loads(body)
    user_name = data.get('name')
    print(f"📥 [Worker] 收到任务: 注册用户 {user_name}")
    send_email_simulation(user_name)

    # 从MQ冲删除这条消息 (ACK)
    ch.basic_ack(delivery_tag=method.delivery_tag)


def start_worker():
    connection = connect_mq()
    channel = connection.channel()
    channel.queue_declare(queue='email_queue', durable=True)
    channel.basic_qos(prefetch_count=1)

    channel.basic_consume(queue='email_queue', on_message_callback = callback)
    print(' [*] 等待任务中... 按 CTRL+C 退出')
    channel.start_consuming()

if __name__ == '__main__':
    try:
        start_worker()

    except Exception as e:
        print(f"连接失败，请确保 Docker RabbitMQ 已启动: {e}")
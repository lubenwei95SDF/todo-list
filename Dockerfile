From python:3.11-slim
RUN rm -rf /etc/apt/sources.list.d/* \
    && echo "deb https://mirrors.aliyun.com/debian/ bookworm main contrib non-free non-free-firmware" > /etc/apt/sources.list \
    && echo "deb https://mirrors.aliyun.com/debian-security/ bookworm-security main contrib non-free non-free-firmware" >> /etc/apt/sources.list \
    && echo "deb https://mirrors.aliyun.com/debian/ bookworm-updates main contrib non-free non-free-firmware" >> /etc/apt/sources.list \
    && apt-get update \
    && apt-get install -y cron
WORKDIR /app

copy requirements.txt requirements.txt

run pip install --no-cache-dir -r requirements.txt

copy . .


run (crontab -l 2>/dev/null; echo "0 1 * * * python /app/check_ddl.py >> /var/log/cron.log 2>&1") | crontab -

run touch /var/log/cron.log


expose 8000

cmd ["gunicorn","-w", "4", "-b", "0.0.0.0:8000", "app:app"]
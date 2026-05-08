FROM alpine:3.21

RUN apk add --no-cache postgresql-client dcron openssl curl

WORKDIR /app

COPY backup.sh .
COPY crontab .

RUN chmod +x backup.sh
RUN crontab crontab

CMD ["sh", "-c", "crond -L /var/log/cron.log && tail -f /var/log/cron.log"]

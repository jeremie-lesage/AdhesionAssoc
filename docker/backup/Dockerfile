FROM alpine:latest

RUN apk add --no-cache postgresql-client cron openssl curl

WORKDIR /app

COPY backup.sh .
COPY crontab .

RUN chmod +x backup.sh
RUN crontab crontab

CMD ["crond", "-f", "-L", "/var/log/cron.log"]
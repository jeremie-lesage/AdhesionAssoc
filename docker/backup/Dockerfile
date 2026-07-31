FROM alpine:3.21

# `openssh-client` + `sshpass` : le transfert passe en SFTP, le cluster OVH
# n'implémentant pas AUTH TLS (cf. backup.sh). `curl` reste utile pour diagnostiquer
# depuis le conteneur.
RUN apk add --no-cache postgresql-client dcron openssl curl openssh-client sshpass

WORKDIR /app

COPY backup.sh .
COPY crontab .

RUN chmod +x backup.sh
RUN crontab crontab

CMD ["sh", "-c", "crond -L /var/log/cron.log && tail -f /var/log/cron.log"]

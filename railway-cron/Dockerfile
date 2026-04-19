# Imagen mínima: un POST al backend y el proceso termina (adecuado para Railway Cron).
# https://github.com/curl/curl-container
FROM curlimages/curl:8.10.1

USER root
COPY entrypoint.sh /entrypoint.sh
RUN chmod 755 /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]

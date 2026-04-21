ARG BUILD_FROM
FROM $BUILD_FROM

RUN apk add --no-cache python3 py3-pip git openssh-client

WORKDIR /app

COPY requirements.txt ./
RUN pip3 install --break-system-packages --no-cache-dir -r requirements.txt

COPY server.py index.html ./
COPY run.sh /run.sh
RUN chmod a+x /run.sh

CMD [ "/run.sh" ]

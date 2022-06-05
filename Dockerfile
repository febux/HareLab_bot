FROM python:3.8-alpine


RUN mkdir -p /usr/src/bot/
WORKDIR /usr/src/bot/

VOLUME /usr/src/bot/bot/data

COPY . .
RUN pip install -r requirements.txt


ENTRYPOINT cd bot && python bot.py
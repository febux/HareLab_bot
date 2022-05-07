FROM python:3.8.13-slim


RUN mkdir -p /usr/src/bot/
WORKDIR /usr/src/bot/

VOLUME /usr/src/bot/bot/data

COPY . .
RUN pip install -r requirements.txt


CMD cd bot && python bot.py
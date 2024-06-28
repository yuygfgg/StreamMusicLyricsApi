FROM python:3.9.19-slim

WORKDIR /app

COPY . /app

RUN pip install -r requirements.txt

COPY start.sh /app/start.sh

RUN mkdir /lyrics

CMD ["bash", "start.sh"]
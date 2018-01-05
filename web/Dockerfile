FROM python:3.6-slim

WORKDIR /app
RUN mkdir -p images

ADD app.py requirements.txt templates static /app/

RUN apt-get update && apt-get install -y libpq-dev
RUN pip install -r requirements.txt

CMD python app.py

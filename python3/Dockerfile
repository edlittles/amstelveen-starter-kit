FROM python:3-alpine

COPY ./requirements.txt /app/requirements.txt
COPY ./helpers.py /app/helpers.py
COPY ./agent.py /app/agent.py
WORKDIR /app
RUN python -m pip install -r requirements.txt
RUN python -m unittest
COPY . /app/
ENTRYPOINT PYTHONUNBUFFERED=1 python agent.py
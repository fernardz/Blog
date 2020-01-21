FROM python:3.7-slim-buster

RUN mkdir /app
WORKDIR /app

COPY . .

RUN pip install pymodbus
RUN pip install twisted

CMD ["python","updating_server.py"]

EXPOSE 5020

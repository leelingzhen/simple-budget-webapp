# syntax=docker/dockerfile:1
FROM python:3.6.9
WORKDIR /budget
COPY ./requirements.txt ./requirements.txt
RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt
COPY . .
CMD ["uwsgi", "--protocol=http", "-w", "application:app", "--socket", "0.0.0.0:5050"]

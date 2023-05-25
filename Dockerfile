FROM python:3.8-slim-buster

WORKDIR /dependencies

COPY requirements.txt requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

COPY dependencies .

ENTRYPOINT ["tail", "-f", "/dev/null"]

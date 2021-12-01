FROM python:3.6-slim

RUN mkdir -p /usr/src/octo
WORKDIR /usr/src/octo
COPY . /usr/src/octo

RUN pip install --no-cache-dir -r requirements.txt

ENV TZ Europe/Moscow
ENV OCTO_MODE default
ENV OCTO_REQUEST default

CMD ["python3", "octo.py"]
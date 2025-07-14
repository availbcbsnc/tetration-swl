FROM python:3-alpine

COPY . /app
WORKDIR /app

RUN apk add --no-cache git bash && \
    pip install /app

RUN echo "anything2annotations --help" >> /root/.bashrc
CMD ["/bin/bash"]

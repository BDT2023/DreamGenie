#FROM python:3.10-slim
FROM ghcr.io/opennmt/ctranslate2:3.19.0-ubuntu20.04-cuda11.2
ARG DEBIAN_FRONTEND=noninteractive
ENTRYPOINT []

WORKDIR /python-docker

COPY requirements.txt requirements.txt
RUN apt-get update && apt-get install git -y
RUN pip3 install -r requirements.txt --user
RUN pip3 install faster-whisper --user
RUN apt-get install -y ffmpeg

COPY . .

EXPOSE 5000

CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0"]


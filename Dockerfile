FROM python

RUN apt-get update \
 && DEBIAN_FRONTEND=noninteractive \
    apt-get install --no-install-recommends --assume-yes \
      portaudio19-dev \
	  redis-server
	  

RUN git clone -b Daniel_experimental https://github.com/BDT2023/DreamGenie.git

COPY Scene_Analyzer/my_secrets.py DreamGenie/Scene_Analyzer/my_secrets.py 

COPY my_secrets.py DreamGenie/my_secrets.py 

COPY Utils/my_secrets_ut.py DreamGenie/Utils/my_secrets_ut.py

COPY Image_Generation/my_secrets_ig.py DreamGenie/Image_Generation/my_secrets_ig.py

COPY WebGui/app.py DreamGenie/WebGui/app.py

RUN pip install --no-cache-dir --upgrade -r DreamGenie/requirements.txt \
    && pip install --no-cache-dir --upgrade -r DreamGenie/WebGui/requirements.txt

WORKDIR DreamGenie/WebGui

CMD ["gunicorn", "app:app", "--worker-class", "eventlet", "--certfile=server.crt" ," --keyfile=server.key", "--bind", "0.0.0.0:5000"]

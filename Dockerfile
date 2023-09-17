FROM python

RUN apt-get update \
 && DEBIAN_FRONTEND=noninteractive \
    apt-get install --no-install-recommends --assume-yes \
      portaudio19-dev \
	  redis-server
	  

RUN git clone -b Daniel_experimental https://github.com/BDT2023/DreamGenie.git

RUN pip install pymongo

#COPY Scene_Analyzer/my_secrets.py DreamGenie/Scene_Analyzer/my_secrets.py 

#COPY my_secrets.py DreamGenie/my_secrets.py 
#COPY WebGui/my_secrets_web.py DreamGenie/WebGui/my_secrets_web.py

#COPY Utils/my_secrets_ut.py DreamGenie/Utils/my_secrets_ut.py

#COPY Image_Generation/my_secrets_ig.py DreamGenie/Image_Generation/my_secrets_ig.py

#COPY WebGui/app.py DreamGenie/WebGui/app.py

RUN pip install -r DreamGenie/requirements.txt \
    && pip install -r DreamGenie/WebGui/requirements.txt

WORKDIR DreamGenie/WebGui

CMD ["gunicorn", "app:app", "--worker-class", "eventlet", "--bind", "0.0.0.0:5000"]

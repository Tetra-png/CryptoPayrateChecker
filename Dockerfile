FROM python:3

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN mkdir ./settings && chmod 777 ./settings

COPY *.py ./

CMD python main.py -d 20 -url1 $URL1 -url2 $URL2 
FROM python:3

RUN apt-get update && apt-get upgrade -y

RUN apt-get install -y libfreetype6-dev libatlas-base-dev liblapack-dev gfortran cron

RUN pip install matplotlib
RUN pip install pandas
RUN pip install bottle

RUN mkdir /bitchart-api
ADD chart.py /bitchart-api/
ADD task.py /bitchart-api/

RUN echo '* * * * * root python /bitchart-api/task.py' >> /etc/crontab

RUN apt-get clean

ENV PRODUCTION true
ENV PORT 8080
ENV TIME_ZONE Asia/Tokyo
EXPOSE ${PORT}
CMD cron && python /bitchart-api/task.py && python /bitchart-api/chart.py

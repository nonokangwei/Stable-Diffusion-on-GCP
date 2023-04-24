FROM python:3.10-bullseye

COPY ./requirements.txt /app/requirements.txt
RUN pip3 install -r /app/requirements.txt

COPY ./* /app/

CMD /app/run.sh

FROM python:3.8-slim-buster

RUN apt-get update && apt-get upgrade -y
RUN apt-get install -y git xvfb

RUN mkdir /lbaf
RUN git clone https://github.com/DARMA-tasking/LB-analysis-framework.git /lbaf
WORKDIR /lbaf
RUN git checkout develop
RUN mkdir /lbaf/in
RUN mkdir /lbaf/out
RUN pip install virtualenv
RUN virtualenv --python /usr/local/bin/python3.8 venv
RUN /bin/sh venv/bin/activate && pip install -r requirements.txt

ENV PYTHONPATH /lbaf/venv/lib/python3.8/site-packages:/lbaf:/lbaf/src
ENV DISPLAY :99.0
COPY entrypoint.sh /lbaf/entrypoint.sh
RUN ["chmod", "+x", "/lbaf/entrypoint.sh"]
ENTRYPOINT ["/lbaf/entrypoint.sh"]
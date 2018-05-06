FROM python:3.6

WORKDIR /usr/src/pinner

ENV PYTHONPATH /usr/lib/python3.6/site-packages/:/usr/local/lib/python3.6/site-packages/

COPY . .
RUN python setup.py install

ARG CONFIG_FILE=exampleConfig.json

COPY $CONFIG_FILE pinner.json

CMD [ "pinner-start", "/usr/src/pinner/pinner.json", "go-ipfs" ]
FROM python:3.6

WORKDIR /usr/src/pinner

ENV PYTHONPATH /usr/lib/python3.6/site-packages/

COPY . .
RUN ls -lah
RUN python setup.py install

ARG CONFIG_FILE=exampleConfig.json

COPY CONFIG_FILE ipfsconf.json

CMD [ "pinner", "/usr/src/pinner/ipfsconf.json", "ipfs" ]
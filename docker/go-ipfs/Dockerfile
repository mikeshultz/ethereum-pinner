FROM jbenet/go-ipfs:latest

EXPOSE 4001
EXPOSE 5001

WORKDIR /usr/src/go-ipfs

RUN ipfs init

CMD ["daemon", "--enable-gc", "--migrate"] 
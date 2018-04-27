FROM jbenet/go-ipfs:latest

EXPOSE 4001
EXPOSE 5001

WORKDIR /usr/src/go-ipfs
#COPY ./ipfsconf.json .
#RUN ipfs config replace /usr/src/go-ipfs/ipfsconf.json
RUN ipfs init

CMD ["daemon", "--enable-gc", "--migrate"] 
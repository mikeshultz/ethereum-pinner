FROM jbenet/go-ipfs:latest

EXPOSE 4001

WORKDIR /usr/src/go-ipfs
RUN ls -lah
COPY ./ipfsconf.json .
RUN ls -lah
RUN pwd
#RUN ipfs config replace /usr/src/go-ipfs/ipfsconf.json
RUN ipfs init

#CMD ["/usr/bin/ipfs", "daemon", "--enable-gc", "--migrate"] 
CMD ["daemon", "--enable-gc", "--migrate"] 
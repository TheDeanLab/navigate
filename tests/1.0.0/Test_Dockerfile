FROM ubuntu:18.04
LABEL author="Jon Gesell"

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update -y --fix-missing && \
  apt-get upgrade -y && \
  apt-get dist-upgrade -y && \
  apt-get autoremove -y && \
  apt-get update -y --fix-missing && \
  apt-get upgrade -y
RUN locale
RUN apt-get install -y gcc g++ apt-utils wget gzip pigz pbzip2 zip software-properties-common make parallel pandoc git

RUN while parallel --citation; do echo "will cite"; done

ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

VOLUME /var/tmp/results
VOLUME /var/tmp/data
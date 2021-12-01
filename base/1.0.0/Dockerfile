# syntax=docker/dockerfile:1

#FROM ubuntu:18.04
#LABEL author="Kevin Dean"
#ENV DEBIAN_FRONTEND=noninteractive

# Install miniconda
#RUN wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
# RUN bash Miniconda3-latest-Linux-x86_64.sh -b -p /miniconda
# ENV PATH=$PATH:/miniconda/condabin:/miniconda/bin

FROM python:3.7-alpine AS base
WORKDIR /1.0.0
RUN pip3 install -r requirements.txt

# Install miniconda environment
#RUN conda create -n ASLM python=3.7.11
#RUN conda activate ASLM
#RUN python -m pip install -r requirements.txt

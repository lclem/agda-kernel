FROM crosscompass/ihaskell-notebook:latest

#haskell:latest

#8.4.3

#fpco/stack-build:lts-13.21

#python:3.7-slim

#crosscompass/ihaskell-notebook:62631e7176e8

LABEL maintainer="Lorenzo Clemente <clementelorenzo@gmail.com>"

USER root

RUN apt-get update
RUN apt-get install --yes apt-utils ghc cabal-install zlib1g-dev libncurses5-dev software-properties-common 

#agda=2.6.1 agda-mode agda-stdlib

# python3-pip

ARG NB_USER=jovyan
ARG NB_UID=1000
ENV USER ${NB_USER}
ENV NB_UID ${NB_UID}
ENV HOME /home/${NB_USER}

# RUN adduser --disabled-password \
#     --gecos "Default user" \
#     --uid ${NB_UID} \
#     ${NB_USER}

USER $NB_UID

RUN cabal update
RUN cabal install alex happy Agda-2.6.1.1

RUN python -m pip install --upgrade pip
RUN python -m pip install --upgrade notebook
RUN python -m pip install --upgrade jupyterlab
RUN python -m pip install jupyterlab-git
RUN python -m pip install jupyter_contrib_nbextensions
RUN python -m pip install widgetsnbextension
RUN python -m pip install jupyterthemes
RUN python -m pip install agda_kernel
RUN python -m agda_kernel.install

RUN jupyter lab build

#ENV JUPYTER_ENABLE_LAB=yes

# Make sure the contents of our repo are in ${HOME}
COPY . ${HOME}
USER root
RUN chown -R ${NB_UID} ${HOME}
USER ${NB_USER}
WORKDIR ${HOME}

ENV PATH ${PATH}:${HOME}/.cabal/bin

RUN jupyter labextension install @jupyterlab/github

RUN make codemirror-install
RUN python -m pip install -r requirements.txt

RUN jupyter contrib nbextension install --user
RUN jupyter nbextension enable --py widgetsnbextension
RUN jupyter nbextension enable agda-extension/main
RUN jupyter nbextension enable toc2/main

#RUN jupyter nbextension enable literate-markdown/main
#RUN jupyter nbextension enable hide_input/main
#RUN jupyter nbextension enable init_cell/main
#RUN jupyter nbextension enable freeze/main

# change theme with jupyter-themes
RUN jt -t grade3 -f roboto -fs 10 -cellw 800 -altp -T
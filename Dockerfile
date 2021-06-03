FROM jupyter/base-notebook

USER root
RUN apt update && apt autoclean -y && apt autoremove -y && apt upgrade -y && apt install gcc python3-dev libgl1-mesa-glx ffmpeg libsm6 libxext6  -y


EXPOSE 8888

RUN pip install matplotlib docker pyyaml #open3d laserchicken

COPY docker/helper_dummy/classifiers.ipynb /home/jovyan/work


COPY . src
WORKDIR src
RUN python setup.py install
RUN jupyter serverextension enable --py fair-cells
RUN jupyter nbextension install --py fair-cells
RUN jupyter nbextension enable fair-cells  --py
WORKDIR ../
RUN rm -r src

ENTRYPOINT jupyter notebook -y --port=8888 --no-browser --allow-root --debug

#
#ENTRYPOINT cd /src && \
#           python setup.py install &&\
#           jupyter serverextension enable --py fair-cells && \
#           jupyter nbextension install --py fair-cells && \
#           jupyter nbextension enable fair-cells  --py && \
#
#           jupyter notebook -y --port=8888 --no-browser --allow-root --debug

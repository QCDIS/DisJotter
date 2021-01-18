"""
POC: Create a Docker container from a Python script.
"""
import json
import sys
import os
import random
import string

import docker

import traceback
from pathlib import Path
import logging
logger = logging.getLogger('DockerService')
logger.setLevel(logging.DEBUG)
from os.path import expanduser

#  Small hack so we can use a dockerfile string instead of having to write it
#  to disk first. See:
#  https://github.com/docker/docker-py/issues/2105#issuecomment-613685891
docker.api.build.process_dockerfile = \
    lambda dockerfile, _: ('Dockerfile', dockerfile)



class DockerService:
    def __init__(self,):
        # self.folder = folder
        # self.name = image_name
        # self.base_image = base_image
        self.client = docker.from_env()

    def get_dockerfile(self,base_image) -> str:
        return (
            "\n".join([
                f'FROM {base_image}',
                f'USER root',
                f'WORKDIR /src/',

                f'COPY ./fair-cells/ /src/fair-cells/',
                f"RUN pip install -r /src/fair-cells/helper/helper_requirements.txt",

                f'COPY ./environment.yml /src/environment.yml',
                f"RUN conda env update --file environment.yml --name base",

                f"USER $NB_UID",

                f'COPY ./notebook.ipynb /src/notebook.ipynb',
                f'COPY ./nb_helper_config.json /src/nb_helper_config.json',

                f'ENTRYPOINT ["python", "-m", "fair-cells"]'
            ])
        )

    def build_container(self, dockerfile: str, folder, image_name) -> docker.api.image.ImageApiMixin:
        #  Save working directory so we can reset it later
        wd = os.getcwd()
        os.chdir(folder)
        logging.info("getcwd: " + str(wd))
        try:
            logging.info("dockerfile: "+str(dockerfile))
            logging.info("Start building container. self.client.images.build")

            image, log = self.client.images.build(tag=image_name,
                                            path='.',
                                            dockerfile=dockerfile,
                                            rm=True,
                                            nocache=True)
        except Exception as e:
            logging.error(traceback.format_exc())
        finally:
            #  Change back
            os.chdir(wd)
        logging.info("Returning image and log: "+str(log))
        return image, log


    def run_container(self, port=10000, image=None) -> docker.api.container.ContainerApiMixin:
        try:
            self.stop_image(image=image)
        except docker.errors.NotFound:
            pass
        logging.info("containers.run name: " + image + " ports: " + str(port))
        container_out = self.client.containers.run(image,
                                   # name=image,
                                   ports={'8888': port},
                                   remove=True,
                                   detach=True)
        return container_out

    def login(self,url=None,username=None,token=None):
        self.username = username
        self.password = token
        self.registry = url
        home_dir = str(Path.home())
        conf_dir = home_dir+'/.docker/'

        if not os.path.exists(conf_dir):
            os.makedirs(conf_dir)
        self.dockercfg_path = conf_dir + '/auth.json'
        if not os.path.exists(self.dockercfg_path):
            with open(self.dockercfg_path, 'w'): pass
        auth = {'username':self.username ,'password':self.password,'registry':self.registry}
        with open(self.dockercfg_path, 'w') as fp:
            json.dump(auth, fp)
        logging.info(str(auth))
        resp = self.client.login(username=username, password=token, registry=url)
        logging.info("resp: " + str(resp))
        return resp

    def get_local_images(self,tag=None):
        images = []
        for image in self.client.images.list():
            if image.tags:
                if tag:
                    for im_tag in image.tags:
                        if tag in im_tag:
                            ret_image = {'name': im_tag}
                            # ret_image['short_id'] = image.short_id
                            images.append(ret_image)
                elif not tag:
                    ret_image = {'name': image.tags[0]}
                    # ret_image['short_id'] = image.short_id
                    images.append(ret_image)
        return images

    def push(self,images):
        logging.info("images: " + str(images))
        results = []
        home_dir = str(Path.home())
        conf_dir = home_dir + '/.docker/'
        dockercfg_path = conf_dir + '/auth.json'

        with open(dockercfg_path) as json_file:
            auth = json.load(json_file)

        resp = self.client.login(username=auth['username'], password=auth['password'], registry=auth['registry'])
        logging.info("resp: " + str(resp))
        for image in images:
            push_resp = None
            if isinstance(image,str):
                logging.info("Pushing: " + str(image))
                push_resp = self.client.images.push(image)
            elif isinstance(image,dict):
                logging.info("Pushing: " + str(image['name'].split(':')[0]))
                push_resp = self.client.images.push(image['name'].split(':')[0])
            logging.info("re: " + str(push_resp))
            results.append(push_resp)
        return results

    def get_image_status(self, image=None):
        running_containers = self.get_container(image_name=image)
        stats = []
        if running_containers:
            for cont in running_containers:
                stats.append( cont.status )
        return stats

    def stop_image(self, image=None):
        running_containers = self.get_container(image_name=image)
        stats = []
        if running_containers:
            for cont in running_containers:
                stats.append(cont.stop(timeout=1))
        return stats

    def get_container(self, image_name=None):
        running_containers = self.client.containers.list()
        if not image_name:
            return running_containers
        if running_containers:
            for cont in running_containers:
                    for tag in cont.image.tags:
                        if tag.split(':')[0] == image_name:
                            return [cont]
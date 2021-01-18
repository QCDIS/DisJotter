import json
import os
import tempfile
import shutil
import importlib

from typing import Optional

import docker
from notebook.base.handlers import IPythonHandler, APIHandler, HTTPError
from notebook.utils import url_path_join

from ..container.docker_service import DockerService
from .base_handler import BaseHandler
from .environment_handler import BASE_STRING

import logging
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


def create_config(notebook_path, cell_index, variables):
    return json.dumps({
        'path': notebook_path,
        'index': cell_index,
        'variables': variables
    })


class BuildDockerFileHandler(BaseHandler):

    def post(self, path):        
        notebook = self.contents_manager.get(path, content=True)
        notebook_path = os.path.join(os.getcwd(), path)

        notebook_name = "notebook.ipynb"

        body = self.get_json_body()

        image_name = body.get('imageName')
        base_image = body.get('baseImage')
        cell_index = int(body.get('cellIndex'))
        variables = body.get('variables', {})
        logging.info("image_name: " + str(image_name))
        logging.info("base_image: " + str(base_image))
        logging.info("cell_index: " + str(cell_index))
        logging.info("variables: " + str(variables))
        if image_name is None or base_image is None or cell_index is None:
            raise HTTPError(400, 'abc')

        requirements = body.get('environment', BASE_STRING)

        #  Create a temporary dir which will be our build context.
        with tempfile.TemporaryDirectory() as tmpdir:
            shutil.copyfile(notebook_path, tmpdir + "/" + notebook_name)

            #  Find the location of the FAIR-Cells module on disk
            #  So it can copy & install it in the container.
            dirname = os.path.dirname(__file__)
            nested_levels = len(__name__.split('.')) - 2
            module_path = os.path.join(dirname + '/..' * nested_levels)

            #  Copy helper to build context.
            shutil.copytree(module_path,
                tmpdir + "/fair-cells/",
                ignore=shutil.ignore_patterns('.ipynb_checkpoints', '__pycache__'))

            with open(tmpdir + "/environment.yml", "a") as reqs:
                reqs.write(requirements)

            with open(tmpdir + "/nb_helper_config.json", "a") as cfg:
                config = create_config(notebook_name, cell_index, variables)
                cfg.write(config)

            with open(tmpdir + "/.dockerignore", "a") as ignore:
                ignore.write("**/backend\n")
                ignore.write("**/frontend\n")

            cc = DockerService()
            docker_file = cc.get_dockerfile(base_image)


        self.finish(json.dumps({
            'dockerFile': docker_file
        }))




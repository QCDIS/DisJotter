import json
import logging
import requests
import sys

from .base_handler import BaseHandler
from ..container.docker_service import DockerService

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)



class DockerImagesHandler(BaseHandler):

    def post(self, path):
        body = self.get_json_body()

        ds = DockerService()
        images = ds.get_local_images()
        logging.info("resp: " + str(images))
        self.finish(json.dumps(images))



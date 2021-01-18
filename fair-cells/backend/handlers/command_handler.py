import json
import os

from typing import Optional

import docker
from notebook.base.handlers import APIHandler, HTTPError

from ..container.docker_service import DockerService
from .base_handler import BaseHandler


class CommandHandler(BaseHandler):
    def post(self, image_name, command):
        if command == 'run':
            return self._run(image_name)
        elif command == 'stop':
            return self._stop(image_name)

        raise HTTPError(400, 'no_cmd')

    def get(self, image_name, command):
        if command == 'status':
            return self._status(image_name)

        raise HTTPError(400, 'no_cmd')

    def _stop(self, image_name):
        client = docker.from_env()
        
        try:
            cc = DockerService()
            status = cc.stop_image(image=image_name)
            if not status:
                status = ['not_found']
        except docker.errors.NotFound:
            status = 'not_found'
        finally:
            self.finish(json.dumps({
                'data': status[0]
            }))

    def _run(self, image_name):
        body = self.get_json_body()
        port = self._int_body('port', 10000)

        if port is None:
            raise HTTPError(400, 'def')


        cc = DockerService()
        container = cc.run_container(port=port,image=image_name)

        self.finish(json.dumps({
            'data': container.status
        }))

    def _status(self, image_name):
        client = docker.from_env()

        try:
            cc = DockerService()
            status = cc.get_image_status(image_name)
            if not status:
                status=['not_found']
        except docker.errors.NotFound:
            status = 'not_found'
        finally:
            self.finish(json.dumps({
                'data': status[0]
            }))


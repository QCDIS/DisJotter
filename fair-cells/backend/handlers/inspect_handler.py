import json
import os
import importlib

from typing import Optional

import docker
from notebook.base.handlers import APIHandler, HTTPError

from ..container.docker_service import DockerService
from .base_handler import BaseHandler

class InspectHandler(BaseHandler):
    def _get_inspector(self, notebook):
        kernel = notebook['content']['metadata']['kernelspec']['name']

        try:
            inspector_module = importlib.import_module(
                f'.inspection.{kernel}', package="fair-cells")

            inspector = inspector_module.inspector()
            
            if inspector.available():
                return inspector
        except ModuleNotFoundError:
            pass

        raise HTTPError(501, 'inspector_unavailable')


    def get(self, path, command):
        notebook = self.contents_manager.get(path, content=True)
        inspector = self._get_inspector(notebook)

        if command == 'available':
            self.set_status(201)
            self.finish()
        elif command == 'variables':
            cell_index = self._int_argument('cellIdx')

            if cell_index is None:
                raise HTTPError(400, 'invalid_cell_idx')

            variables = inspector.get_variables(notebook, cell_index)

            self.finish(json.dumps({
                'data': variables
            }))
        elif command == "inspector.html":
            cell_index = self._int_argument('cellIdx')

            if cell_index is None:
                raise HTTPError(400, 'invalid_cell_idx')

            self.render("inspector.html", **{
                'variables': inspector.get_variables(notebook, cell_index)
            })
        else:
            raise HTTPError(400, 'no_cmd')

    def post(self, path, command):
        pass

    def get_template_path(self):
        dirname = os.path.dirname(__file__)

        return os.path.join(dirname + "/../templates")

from fabric import Connection
from collections import OrderedDict
from .utils import run_as_root


class GitService:

    def __init__(self, connection: Connection, config: OrderedDict):
        self.conn: Connection = connection
        self.config: OrderedDict = config
        self.project_name = self.config.get('PROJECT_NAME', 'django_app')
        self.project_root = self.config.get('PROJECT_ROOT', f'webapps/{self.project_name}')

    def clone_project(self, repo: str):
        """
            Clonar proyecto desde repositorio
        """
        run_as_root(self.conn, f'mkdir -p {self.project_root} && cd {self.project_root} && git clone {repo} .')

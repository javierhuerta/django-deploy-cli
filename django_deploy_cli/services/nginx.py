from os import path
from fabric import Connection
from jinja2 import Template
from collections import OrderedDict
from .utils import run_as_root
from .constants import TEMPLATES_DIR


class NginxService:

    def __init__(self, connection: Connection, config: OrderedDict):
        self.conn: Connection = connection
        self.config: OrderedDict = config
        self.project_name = self.config.get('PROJECT_NAME', 'django_app')
        self.nginx_filename = f'{self.project_name}.conf'
        self.socket_name = f'{self.project_name}.sock'

    def enable(self):
        run_as_root(self.conn, f'mkdir -p {self.config.get("PROJECT_ROOT")}logs')
        run_as_root(self.conn, f'touch {self.config.get("PROJECT_ROOT")}logs/nginx-access.log')
        run_as_root(self.conn, f'touch {self.config.get("PROJECT_ROOT")}logs/nginx-error.log')
        run_as_root(self.conn, f'ln -s /etc/nginx/sites-available/{self.nginx_filename} /etc/nginx/sites-enabled')
    
    def create_nginx_conf(self):
        template = Template(open(path.join(TEMPLATES_DIR, 'nginx.conf')).read())
        result = template.render(
            server_domain=self.config.get('DOMAIN', 'example.com'),
            access_log=f'{self.config.get("PROJECT_ROOT")}logs/nginx-access.log',
            error_log=f'{self.config.get("PROJECT_ROOT")}logs/nginx-error.log',
            static_path=f'{self.config.get("PROJECT_ROOT")}static/',
            media_path=f'{self.config.get("PROJECT_ROOT")}media/',
            socket_path=f'http://unix:/run/{self.socket_name}'
        )
        
        with open(f'{self.nginx_filename}', 'w') as file:
            file.write(result)
            file.close()

        self.conn.put(f'{self.nginx_filename}', '/etc/nginx/sites-available/')

from fabric import Connection
from jinja2 import Template
from collections import OrderedDict
from os import path
from .utils import run_as_root
from .constants import TEMPLATES_DIR


class GunicornService:

    def __init__(self, connection: Connection, config: OrderedDict):
        self.conn: Connection = connection
        self.config: OrderedDict = config
        self.project_name = self.config.get('PROJECT_NAME', 'django_app')
        self.socket_file = f'{self.project_name}.socket'
        self.gunicorn_service_file = f'{self.project_name}.service'
        self.socket_name = f'{self.project_name}.sock'
        self.project_wsgi = f'{self.project_name}.wsgi:application'

    def start_enable(self):
        run_as_root(self.conn, f'systemctl start {self.socket_file}')
        run_as_root(self.conn, f'systemctl enable {self.socket_file}')

    def status(self):
        run_as_root(self.conn, f'systemctl status {self.socket_file}')
        
    def create_systemd_socket(self):
        #run_as_root(self.conn, f'touch /etc/systemd/system/{self.socket_file}')

        template = Template(open(path.join(TEMPLATES_DIR, 'gunicorn.socket')).read())
        result = template.render(description=f'{self.project_name} socket', socket_name=self.socket_name)
        with open(f'{self.socket_file}', 'w') as file:
            file.write(result)
            file.close()

        self.conn.put(f'{self.socket_file}', '/etc/systemd/system/')

    def create_gunicorn_service(self):
        """
            Crear servicio
        """
        #run_as_root(self.conn, f'touch /etc/systemd/system/{self.gunicorn_service_file}')

        template = Template(open(path.join(TEMPLATES_DIR, 'gunicorn.service')).read())
        result = template.render(
            description=f'Gunicorn deamon for {self.project_name} project', 
            socket_file=self.socket_file,
            user=self.config.get('USER'),
            group=self.config.get('GROUP'),
            project_root=self.config.get('PROJECT_ROOT'),
            gunicorn_bin=f'{self.config.get("PROJECT_ENV")}bin/gunicorn',
            socket_name=self.socket_name,
            project_wsgi=self.project_wsgi
        )

        with open(f'{self.gunicorn_service_file}', 'w') as file:
            file.write(result)
            file.close()

        self.conn.put(f'{self.gunicorn_service_file}', '/etc/systemd/system/')

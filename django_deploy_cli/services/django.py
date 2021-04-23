from os import path, remove
from fabric import Connection
from jinja2 import Template
from collections import OrderedDict
from .utils import run_as_root
from .constants import TEMPLATES_DIR


class DjangoService:

    def __init__(self, connection: Connection, config: OrderedDict):
        self.conn: Connection = connection
        self.config: OrderedDict = config
        self.project_name = self.config.get('PROJECT_NAME', 'django_app')
        self.config_filename_production = 'env.production'
        self.socket_file = f'{self.project_name}.socket'

    def copy_env_production(self):
        template = Template(open(path.join(TEMPLATES_DIR, 'env-production')).read())
        result = template.render(
            web_domain=self.config.get('DOMAIN'),
            django_settings_module=self.config.get('DJANGO_SECRET_MODULE'),
            django_secret_key=self.config.get('DJANGO_SECRET_KEY'),
            group=self.config.get('GROUP'),
            user=self.config.get('USER'),
            sql_engine=self.config.get('SQL_ENGINE'),
            sql_database=self.config.get('SQL_DATABASE'),
            sql_user=self.config.get('SQL_USER'),
            sql_password=self.config.get('SQL_PASSWORD')
        )

        with open(config_filename_production, 'w') as file:
            file.write(result)
            file.close()

        if path.exists(config_filename_production):
            self.conn.put(config_filename_production, f'{self.config.get("PROJECT_ROOT")}')
            remove(config_filename_production)

    def deploy(self):
        with self.conn.prefix(f'source {self.config.get("PROJECT_ENV")}bin/activate'):
            with self.conn.cd(f'{self.config.get("PROJECT_ROOT")}'):
                self.conn.run('git pull', pty=True)
                self.conn.run('npm install', pty=True) # En caso que exista un archivo package.json
                self.conn.run('pip install -r requirements/prod.txt', pty=True)
                self.conn.run('python manage.py migrate')
                self.conn.run('python manage.py collectstatic --no-input', pty=True)
        run_as_root(self.conn, f'systemctl restart {self.socket_file}')
        run_as_root(self.conn, f'systemctl nginx reload')

from os import path, remove
from fabric import Connection
from jinja2 import Template
from collections import OrderedDict
from .utils import run_as_root
from .constants import TEMPLATES_DIR


class DebianService:

    def __init__(self, connection: Connection, config: OrderedDict):
        self.conn: Connection = connection
        self.config: OrderedDict = config
        self.project_name = self.config.get('PROJECT_NAME', 'django_app')

    def install_dependencies(self):
        run_as_root(self.conn, f'apt update', pty=True)
        run_as_root(self.conn, f'apt upgrade', pty=True)
        run_as_root(self.conn, f'apt update', pty=True)
        run_as_root(self.conn, f'apt install sudo', pty=True)
        run_as_root(self.conn, f'apt install python3-pip python3-dev libpq-dev postgresql postgresql-contrib nginx curl', pty=True)
        run_as_root(self.conn, f'-H pip3 install --upgrade pip', pty=True)
        run_as_root(self.conn, f'-H pip3 install virtualenv', pty=True)
        run_as_root(self.conn, f'apt install nodejs npm', pty=True)

    def install_firewall(self):
        run_as_root(self.conn, f'apt update', pty=True)
        run_as_root(self.conn, f'apt install ufw')
        run_as_root(self.conn, f'ufw allow OpenSSH')
        run_as_root(self.conn, f'ufw allow {self.config.get("SSH_PORT")}')
        run_as_root(self.conn, f'ufw allow http')
        run_as_root(self.conn, f'ufw allow https')
        run_as_root(self.conn, f'ufw enable')
        run_as_root(self.conn, f'ufw status')

    def install_ssl_dependencies(self):
        run_as_root(self.conn, f'apt update')
        run_as_root(self.conn, f'apt install python3-acme python3-certbot python3-mock python3-openssl python3-pkg-resources python3-pyparsing python3-zope.interface')
        run_as_root(self.conn, f'apt install python3-certbot-nginx')
        
    def install_ssl(self):
        self.conn.run('', )
        run_as_root(self.conn, f'certbot --nginx -d {self.config.get("DOMAIN")}', pty=True)
        #run_as_root(self.conn, f'certbot renew --dry-run')

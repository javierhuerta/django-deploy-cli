import secrets
from fabric import Connection
from invoke import env
from jinja2 import Template
from os import path, remove

CHARS = 'abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)'

def sudo_cd(c: Connection, path, command):
    """Workaround on the problem of cd not working with sudo command"""
    return c.run(f'cd {path} && sudo {command}', hide=True)

def run_as_root(c: Connection, command, *args, **kwargs):
    """
    Run a remote command as the root user.
    When connecting as root to the remote system, this will use Fabric's
    ``run`` function. In other cases, it will use ``sudo``.
    """
    if c.user == 'root':
        func = c.run
    else:
        func = c.sudo
    return func(command, *args, **kwargs)

def generate_django_secret_key():
    length = 50
    chars = 'abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)'
    secret_key = ''.join(secrets.choice(CHARS) for i in range(length))
    return secret_key

def generate_password():
    length = 10
    password = ''.join(secrets.choice(CHARS) for i in range(length))
    return password

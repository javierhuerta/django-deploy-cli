from fabric import Connection
from invoke import env

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

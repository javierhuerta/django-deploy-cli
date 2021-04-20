from fabric import Connection
from .utils import run_as_root

def setup_ufw(c: Connection, config):
    run_as_root(c, f'apt update && apt install ufw', pty=False)
    run_as_root(c, f'ufw allow OpenSSH && ufw allow 22222 && ufw enable && ufw status', pty=False)

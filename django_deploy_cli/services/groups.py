from fabric import Connection
from .utils import run_as_root


def exists(c: Connection, name: str, warn: bool=True):
    """
        Verificar si grupo existe
    """
    return c.run(f'getent group {name}', warn=warn).ok


def create(c: Connection, name, gid=None):
    args = []
    if gid:
        args.append('-g %s' % gid)
    args.append(name)
    args = ' '.join(args)
    run_as_root(c, f'groupadd {args}')
    
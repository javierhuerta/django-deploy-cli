from fabric import Connection
from .utils import run_as_root
from . import groups
from .constants import SYSTEM_GROUP_DEFAULT
from collections import OrderedDict
import typer


class UserService:

    def __init__(self, connection: Connection, config: OrderedDict):
        self.conn: Connection = connection
        self.config: OrderedDict = config

    def exists(self, username: str, warn: bool=True):
        """
            Comprobar si usuario de sistema ya se encuentra creado o no
        """
        return self.conn.run(f'getent passwd {username}', warn=warn).ok

    def create_user(self, username: str, default_group: bool = True):
        """
            Crear usuario
        """
        if default_group:
            # Revisar que el grupo exista en el sistema
            if not groups.exists(self.conn, self.config.get('GROUP', SYSTEM_GROUP_DEFAULT), warn=False):
                typer.secho(f'Creando grupo {self.config.get("GROUP", SYSTEM_GROUP_DEFAULT)} \n', fg=typer.colors.GREEN)
                groups.create(self.conn, self.config.get('GROUP', SYSTEM_GROUP_DEFAULT))
            else:
                typer.secho(f'Grupo {self.config.get("GROUP", SYSTEM_GROUP_DEFAULT)} ya existe \n', fg=typer.colors.YELLOW)

        if not self.exists(username, warn=False):
            self.__create_user_command(username, default_group)
        else:
            typer.secho(f'Usuario {username} ya existe \n', fg=typer.colors.YELLOW)


    def adduser_sudo(self, username: str):
        """
            Añadir permisos de superusuario
        """
        typer.secho(f'Añadiendo permisos de sudo a usuario {username}\n', fg=typer.colors.YELLOW)
        
        if not self.exists(username, warn=False):
            typer.secho(f'Usuario {username} no existe', fg=typer.colors.RED)
            return False

        run_as_root(self.conn, f'usermod -aG sudo {username}', hide=True)

    def __create_user_command(self, username: str, default_group: bool):
        if default_group:
                typer.secho(f'Usuario con grupo {self.config.get("GROUP", SYSTEM_GROUP_DEFAULT)} creado satisfactoriamente \n', fg=typer.colors.GREEN)

                run_as_root(
                    self.conn, 
                    f'useradd --system --gid {self.config.get("GROUP", SYSTEM_GROUP_DEFAULT)} --shell /bin/bash {username}')
        else:
            typer.secho(f'Usuario sin grupo por defecto creado satisfactoriamente \n', fg=typer.colors.GREEN)

            run_as_root(
                self.conn, 
                f'useradd --system --shell /bin/bash {username}')
    
import typer
from fabric import Connection
from collections import OrderedDict
from .utils import run_as_root, sudo_cd


class PostgresService:

    def __init__(self, connection: Connection, config: OrderedDict):
        self.conn: Connection = connection
        self.config: OrderedDict = config

    def _run_as_pg(self, command):
        """
        Ejecutar commando como usuario 'postgres'
        """
        return sudo_cd(self.conn, '~postgres', f'-u postgres {command}')


    def user_exists(self, name):
        """
        Verificar si usuario postgres existe o no
        """
        res = self._run_as_pg('''psql -t -A -c "SELECT COUNT(*) FROM pg_user WHERE usename = '%(name)s';"''' % locals())
        return (res.stdout.strip() == "1")

    def create_user(self, name, password, superuser=False, createdb=False,
        createrole=False, inherit=True, login=True, connection_limit=None,
        encrypted_password=True):
        """
            Crear usuario de forma segura
        """
        if not self.user_exists(name):
            typer.secho(f'Creando usuario de base de datos {name}', fg=typer.colors.BLUE)
            self._create_user_command(name, password, superuser, createdb, createrole, inherit,
                        login, connection_limit, encrypted_password)
        else:
            typer.secho(f'Usuario de base de datos {name} ya existe', fg=typer.colors.YELLOW)


    def create_database(self, name, owner, template='template0', encoding='UTF8',
                locale='es_CL.UTF-8'):
        """
            Crear bd de forma segura 
        """
        if not self.database_exists(name):

            if locale not in self.conn.run('locale -a').stdout.strip().split():
                typer.secho(f'Instalando locale {locale} faltante', fg=typer.colors.BLUE)
                # Falta descomentar respectivo {locale} en archivo /etc/locale.gen
                run_as_root(self.conn, f'locale-gen {locale}')
                self._restart_postgres()

            typer.secho(f'Creando base de datos {name}', fg=typer.colors.BLUE)
            self._create_database_command(name, owner, template=template, encoding=encoding,
                            locale=locale)
        else:
            typer.secho(f'Base de datos {name} ya existe', fg=typer.colors.YELLOW)


    def _create_user_command(self, name, password, superuser=False, createdb=False,
                    createrole=False, inherit=True, login=True,
                    connection_limit=None, encrypted_password=False):
        """
        Crear usuario PostgresSql
        """
        options = [
            'SUPERUSER' if superuser else 'NOSUPERUSER',
            'CREATEDB' if createdb else 'NOCREATEDB',
            'CREATEROLE' if createrole else 'NOCREATEROLE',
            'INHERIT' if inherit else 'NOINHERIT',
            'LOGIN' if login else 'NOLOGIN',
        ]
        if connection_limit is not None:
            options.append('CONNECTION LIMIT %d' % connection_limit)
        password_type = 'ENCRYPTED' if encrypted_password else 'UNENCRYPTED'
        options.append("%s PASSWORD '%s'" % (password_type, password))
        options = ' '.join(options)
        self._run_as_pg('''psql -c "CREATE USER "'"%(name)s"'" %(options)s;"''' % locals())


    def _drop_user_command(self, name):
        """
        Eliminar usuario PostgresSql
        """
        self._run_as_pg('''psql -c "DROP USER %(name)s;"''' % locals())


    def database_exists(self, name):
        """
        Verificar si base de datos existe
        """
        try:
            return self._run_as_pg('''psql -d %(name)s -c ""''' % locals()).ok
        except:
            return False


    def _create_database_command(self, name, owner, template='template0', encoding='UTF8',
                        locale='es_CL.UTF-8'):
        """
        Crear base de datos postgres
        """
        self._run_as_pg('''createdb --owner %(owner)s --template %(template)s \
                    --encoding=%(encoding)s --lc-ctype=%(locale)s \
                    --lc-collate=%(locale)s %(name)s''' % locals())


    def _drop_database(self, name):
        """
        Eliminar base de datos PostgreSQL
        """
        self._run_as_pg(self, '''dropdb %(name)s''' % locals())


    def _create_schema(self, name, database, owner=None):
        """
        Crear schema en bd
        """
        if owner:
            self._run_as_pg('''psql %(database)s -c "CREATE SCHEMA %(name)s AUTHORIZATION %(owner)s"''' % locals())
        else:
            self._run_as_pg('''psql %(database)s -c "CREATE SCHEMA %(name)s"''' % locals())

    def _restart_postgres(self):
        run_as_root(self.conn, 'systemctl restart postgresql')
        
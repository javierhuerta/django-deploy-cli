import typer
import click_spinner
from os import path
from dotenv import dotenv_values, set_key
from fabric import Connection
from jinja2 import Template
from paramiko import AuthenticationException
from paramiko.ssh_exception import NoValidConnectionsError
from .services.users import UserService
from .services.postgres import PostgresService
from .services.gunicorn import GunicornService
from .services.nginx import NginxService
from .services.git import GitService
from .services.firewall import setup_ufw
from .services.utils import generate_django_secret_key, generate_password
from .services.constants import SYSTEM_USER_DEFAULT, SYSTEM_GROUP_DEFAULT, SSH_PORT_DEFAULT, SSH_AUTH_METHOD_DEFAULT, SSH_AUTH_METHOD_PASSWORD
from .services.constants import USER_DB, PASSWORD_DB, NAME_DB, ENV_FILENAME, TEMPLATES_DIR

# App CLI
app = typer.Typer()
# SETTINGS - Config environments
config = dotenv_values(ENV_FILENAME)

@app.command()
def create_envfile():

    can_create_file = True
    if path.exists(ENV_FILENAME):
        can_create_file = typer.confirm(f'El archivo de configuración {ENV_FILENAME} ya existe. ¿Quieres sobreescribirlo?')

    if can_create_file:
        typer.secho(f'Creando archivo de configuración {ENV_FILENAME}...', fg=typer.colors.BLUE)

        web_domain = typer.prompt(f'¿Dominio web de la aplicación?')
        django_settings_module = typer.prompt(f'¿Ruta de python de archivo de settings - DJANGO_SETTINGS_MODULE?')
        auto_secret_key = typer.confirm(f'Quieres autogenerar el Django Secret Key')
        if auto_secret_key:
            django_secret_key = generate_django_secret_key()
        else:
            django_secret_key = typer.prompt(f'¿Django Secret Key?')
        group = typer.prompt(f'¿Grupo de sistema operativo para la aplicación?', default=SYSTEM_GROUP_DEFAULT, show_default=True)
        user = typer.prompt(f'¿Usuario de sistema operativo para la aplicación?')
        project_name = typer.prompt(f'¿Nombre del proyecto? (se usará para el nombre la carpeta y archivos de configuración)')
        project_root = typer.prompt(f'¿Ruta en sistema de archivos dónde quedara alojado la aplicación en el servidor?', default='/webapps/${PROJECT_NAME}/', show_default=True)
        project_env = typer.prompt(f'¿Ruta a virtualenv del aplicativo?', default='${PROJECT_ROOT}env/', show_default=True)
        project_wsgi = typer.prompt(f'¿Ruta de python a archivo wsgi?')
        sql_engine = typer.prompt(f'¿Motor de base de datos para settings en django?', default='django.db.backends.postgresql', show_default=True)
        sql_database = typer.prompt(f'¿Nombre de la base de datos?')
        sql_user = typer.prompt(f'¿Usuario de la base de datos?')
        auto_password = typer.confirm(f'Quieres autogenerar la contraseña para el usuario de base de datos {sql_user}')
        if auto_password:
            sql_password = generate_password()
        else:
            sql_password = typer.prompt(f'¿Contraseña para usuario de la base de datos?')
        
        ssh_user = typer.prompt(f'¿Usuario para conexión ssh con servidor?', default=SYSTEM_USER_DEFAULT, show_default=True)
        ssh_host = typer.prompt(f'¿Dirección del servidor (example.cl)?')
        ssh_port = typer.prompt(f'¿Puerto para conexión ssh con servidor?', default=SSH_PORT_DEFAULT, show_default=True) 
        ssh_auth_method = typer.prompt(f'¿Metodo de conexión ssh (password|keypairs)?', default=SSH_AUTH_METHOD_DEFAULT, show_default=True) 
        git_repo = typer.prompt(f'¿Repositorio git con el código de la aplicación?') 
        git_main_brach_repo = typer.prompt(f'¿Rama principal de git?', default='main', show_default=True)

        template = Template(open(path.join(TEMPLATES_DIR, 'env-deployment')).read())
        result = template.render(
            web_domain=web_domain,
            django_settings_module=django_settings_module,
            django_secret_key=django_secret_key,
            group=group,
            user=user,
            project_name=project_name,
            project_root=project_root,
            project_env=project_env,
            project_wsgi=project_wsgi,
            sql_engine=sql_engine,
            sql_database=sql_database,
            sql_user=sql_user,
            sql_password=sql_password,
            ssh_user=ssh_user,
            ssh_host=ssh_host,
            ssh_port=ssh_port,
            ssh_auth_method=ssh_auth_method,
            git_repo=git_repo,
            git_main_brach_repo=git_main_brach_repo
        )

        with open(f'{ENV_FILENAME}', 'w') as file:
            file.write(result)
            file.close()
        typer.secho(f'Archivo de configuración {ENV_FILENAME} creado satisfactoriamente.', fg=typer.colors.BLUE)

    typer.secho(f'Procedimiento terminado', fg=typer.colors.GREEN)


@app.command()
def setup(
    host: str = typer.Option(config.get('SSH_HOST'), prompt="Ingrese la dirección del servidor (host)", show_default=True), 
    port: int = typer.Option(config.get('SSH_PORT', SSH_PORT_DEFAULT), prompt="Puerto de conexión ssh", show_default=True), 
    user: str = typer.Option(config.get('SSH_USER', SYSTEM_USER_DEFAULT), prompt="Usuario", show_default=True), 
    auth_method: str = config.get('SSH_AUTH_METHOD', SSH_AUTH_METHOD_DEFAULT),
    update_env: bool = True):
    """
        Configurar proyecto django en servidor linux
    """

    if not path.exists(ENV_FILENAME):
        typer.secho(f'Archivo de configuración {ENV_FILENAME} no existe. Primero debe crear este archivo ejecutando el comando "create-envfile".', fg=typer.colors.RED)
        raise typer.Exit()

    dict_conn = {
        'host': host,
        'port': port,
        'user': user,
    }
    if auth_method == SSH_AUTH_METHOD_PASSWORD:
        password = typer.prompt(f'Ingrese contraseña de servidor', hide_input=True)
        dict_conn['connect_kwargs'] = { 'password': password }

    c = Connection(**dict_conn)
    with click_spinner.spinner() as spinner:
        typer.secho(f'Intentando conectar a host {host}...', fg=typer.colors.GREEN)
        try:
            c.open()
            typer.secho(f'Conexión establecida correctamente', fg=typer.colors.BLUE, underline=True)
            if update_env:
                # Actualizar configuraciones en .env
                set_key('.env', 'SSH_HOST', host)
                set_key('.env', 'SSH_PORT', f'{port}')
                set_key('.env', 'SSH_USER', user)
                set_key('.env', 'SSH_AUTH_METHOD', auth_method)

        except AuthenticationException as err:
            typer.secho(f'Fallo en la autentificación', fg=typer.colors.RED, underline=True)
            raise typer.Exit()
        except NoValidConnectionsError as err:
            typer.secho(f'Conexión no valida, revise el host y puerto', fg=typer.colors.RED, underline=True)
            raise typer.Exit()
        finally:
            spinner.stop()

    # Usuario de sistema
    want_create_user = typer.confirm("¿Quieres crear el usuario de sistema?")
    if want_create_user:
        typer.secho("(1) Creando usuario de sistema para app", fg=typer.colors.GREEN)
        system_user = typer.prompt(f'¿Usuario para la aplicación?', default=config.get('USER'), show_default=True)
        user_service = UserService(c, config)
        with click_spinner.spinner() as spinner:
            user_service.create_user(system_user, config)
            user_service.adduser_sudo(system_user)
        del user_service

        if update_env:
            # Actualizar configuraciones en .env
            set_key('.env', 'USER', system_user)

    # Clonar repo
    want_clone_repo = typer.confirm("¿Quieres clonar el repositorio en el servidor?")
    if want_clone_repo:
        typer.secho("(2) Clonar repo en servidor", fg=typer.colors.GREEN)
        repo = typer.prompt(f'¿Repositorio de código para aplicación?', default=config.get('GIT_REPO'), show_default=True)
        git_service = GitService(c, config)
        with click_spinner.spinner() as spinner:
            git_service.clone_project(repo)
        del git_service

    # Base de datos (postgres)
    want_conf_db = typer.confirm("¿Quieres configurar el usuario y base de datos postgres de la aplicación?")
    if want_conf_db:
        typer.secho("(3) Configurando base de datos", fg=typer.colors.GREEN)
        db_user = typer.prompt(f'¿Usuario para la base de datos?', default=config.get('SQL_USER', USER_DB), show_default=True)
        db_password = typer.prompt(f'¿Password para la base de datos? [.env -> SQL_PASSWORD]', default=config.get('SQL_PASSWORD', PASSWORD_DB), show_default=False)
        db_name = typer.prompt(f'¿Nombre de la base de datos?', default=config.get('SQL_DATABASE', NAME_DB), show_default=True)
        database_service = PostgresService(c, config)
        with click_spinner.spinner() as spinner:
            database_service.create_user(db_user, db_password)
            database_service.create_database(db_name, db_user)
        del database_service

        if update_env:
            # Actualizar configuraciones en .env
            set_key('.env', 'USER_DB', db_user)
            set_key('.env', 'SQL_PASSWORD', db_password)
            set_key('.env', 'SQL_DATABASE', db_name)

    # Gunicorn
    want_conf_gunicorn = typer.confirm("¿Quieres configurar los archivos gunicorn para servir la aplicación?")
    gunicorn_service = GunicornService(c, config)
    if want_conf_gunicorn:
        typer.secho("(4) Creando archivos de gunicorn...", fg=typer.colors.GREEN)
        with click_spinner.spinner() as spinner:
            gunicorn_service.create_systemd_socket()
            gunicorn_service.create_gunicorn_service()

    gunicorn_active = typer.confirm("¿Quieres activar el servicio gunicorn?")
    if gunicorn_active:
        gunicorn_service.start_enable()
    del gunicorn_service

    # Nginx
    want_conf_nginx = typer.confirm("¿Quieres configurar el archivo nginx del aplicativo?")
    nginx_service = NginxService(c, config)
    if want_conf_nginx:
        typer.secho("(5) Creando archivos de nginx...", fg=typer.colors.GREEN)
        with click_spinner.spinner() as spinner:
            nginx_service.create_nginx_conf()

    nginx_active = typer.confirm("¿Quieres activar el servidor virtual de nginx de la aplicación?")
    if nginx_active:
        nginx_service.enable()

    typer.secho("Proceso terminado", fg=typer.colors.GREEN)

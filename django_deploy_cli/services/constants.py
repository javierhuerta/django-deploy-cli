from pathlib import Path
from os import path

SSH_AUTH_METHOD_PASSWORD = 'password'
SSH_AUTH_METHOD_KEYS = 'keys'

SYSTEM_GROUP_DEFAULT = 'www-data' # Grupo de servidores web (nginx o apache)
SYSTEM_USER_DEFAULT = 'root'
SSH_PORT_DEFAULT = 22
SSH_AUTH_METHOD_DEFAULT = SSH_AUTH_METHOD_PASSWORD

USER_DB = 'django'
PASSWORD_DB = 'django'
NAME_DB = 'django'

ENV_FILENAME = '.env-deployment'
VIRTUALENV_FOLDERNAME = 'venv'

APP_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = path.join(APP_DIR, 'templates')

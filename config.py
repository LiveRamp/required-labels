import os
import sys
from pathlib import Path

from exceptions import NoGitHubTokenException


APP_BASEDIR = Path(os.path.abspath(__file__)).parent
APP_NAME = "liveramp/required-labels"


class ConfigException(Exception):
    pass


def generate_config():
    config = {}
    
    config['required_any'] = os.environ.get('REQUIRED_LABELS_ANY', None)
    config['required_all'] = os.environ.get('REQUIRED_LABELS_ALL', None)
    config['banned'] = os.environ.get('BANNED_LABELS', None)
    config['github_user'] = os.environ.get('GITHUB_USER', None)
    config['github_pw'] = os.environ.get('GITHUB_PW', None)
    config['github_token'] = os.environ.get('GITHUB_TOKEN', None)
    config['github_status_text'] = os.environ.get('GITHUB_STATUS_TEXT', 'Label requirements not satisfied.')
    config['github_status_url'] = os.environ.get('GITHUB_STATUS_URL', '')

    for label in ['required_any', 'required_all', 'banned']:
        config[label] = config[label].split(',') if config[label] else None
    return config

CONFIG = generate_config()


def get_token():
    if not CONFIG['github_token']:
        raise NoGitHubTokenException
    return CONFIG['github_token']


def get_credentials():
    if CONFIG['github_user'] == '' or CONFIG['github_pw'] == '':
        return None
    return CONFIG['github_user'], CONFIG['github_pw']


UNIT_TESTING = any([arg for arg in sys.argv if 'test' in arg])


if not UNIT_TESTING:
    labels_configured = any([CONFIG['required_any'], CONFIG['required_all'],
                             CONFIG['banned']])
    credentials_configured = any([all([CONFIG['github_pw'], CONFIG['github_user']]),
                                  CONFIG['github_token']])
    if not labels_configured or not credentials_configured:
        raise ConfigException(
            "Please ensure that the environment variables are set.\n"
            "such as REQUIRED_LABELS_ALL, REQUIRED_LABELS_ANY, or BANNED_LABELS along with "
            "GITHUB_TOKEN or GITHUB_USER and GITHUB_PW"
        )

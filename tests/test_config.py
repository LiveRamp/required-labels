import os
import unittest
from unittest.mock import patch

from config import generate_config, APP_BASEDIR


class TestGenerateConfig(unittest.TestCase):
    def test_it_source_config_from_environment_with_missing_conf(self):
        with patch.dict(os.environ, {'CONFIG_FILE': '/conf/notexist',
                                     'GITHUB_USER': 'ghuser'}):
            config = generate_config()
            assert config['github_user'] == 'ghuser'

    def test_it_source_config_from_given_config_file(self):
        fixture_config = os.path.join(APP_BASEDIR, 'tests', 'fixtures',
                                      'custom.conf.test')
        with patch.dict(os.environ, {'CONFIG_FILE': fixture_config}):
            config = generate_config()
            assert config['github_user'] == 'someuser'
            assert config['github_status_text'] == "Label requirements not satisfied"
            assert config['github_status_url'] == "https://somewhere_with_more_information.com"
    
    def test_it_source_config_from_environment(self):
        with patch.dict(os.environ, {'GITHUB_USER': 'ghuser'}):
            config = generate_config()
            assert config['github_user'] == 'ghuser'
import os
import unittest
from unittest.mock import patch

from config import generate_config, APP_BASEDIR


class TestGenerateConfig(unittest.TestCase):
    def test_it_source_config_from_environment(self):
        with patch.dict(os.environ, {'GITHUB_USER': 'ghuser'}):
            config = generate_config()
            assert config['github_user'] == 'ghuser'
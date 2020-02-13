import unittest
from unittest.mock import patch, MagicMock

from exceptions import NoGitHubTokenException
from utils import PullRequest


class TestPullRequest(unittest.TestCase):
    @patch('utils.Session', MagicMock())
    @patch('utils.get_credentials')
    @patch('utils.get_token')
    def test_it_use_login_token_authentication(self,
                                               get_token,
                                               get_credentials):
        get_credentials.return_value = ('myuser', 'mypass')
        PullRequest({'pull_request': {'issue_url': 'https/github/orga/url/issueurl'}})
        get_token.assert_called_once()
        get_credentials.assert_not_called()

    @patch('utils.Session', MagicMock())
    @patch('utils.get_credentials')
    @patch('utils.get_token')
    def test_it_fallback_to_login_password_authentication_with_no_token(self,
                                                                        get_token,
                                                                        get_credentials):
        get_token.side_effect = NoGitHubTokenException
        PullRequest({'pull_request': {'issue_url': 'https/github/orga/url/issueurl'}})
        get_token.assert_called_once()
        get_credentials.assert_called_once()

    @patch('utils.Session', MagicMock())
    @patch('utils.get_proxy')
    def test_it_calls_proxy_config_during_init(self,
                                               get_proxy):
        get_proxy.return_value = 'https://ghproxy.github.com/api/v3/'
        pr = PullRequest({'pull_request': {'issue_url': 'https://api.github.com/orga/url/issueurl'}})
        self.assertEqual(pr.github_proxy, 'https://ghproxy.github.com/api/v3/')

    @patch('utils.Session', MagicMock())
    @patch('utils.get_proxy')
    def test_it_uses_proxy_status_url(self,
                                      get_proxy):
        get_proxy.return_value = 'https://ghproxy.github.com/api/v3/'
        pr = PullRequest({'pull_request': {'statuses_url': 'https://api.github.com/orga/url/statuses_url', 'issue_url': 'https://api.github.com/orga/url/issueurl'}})
        self.assertEqual(pr.statuses_url, 'https://ghproxy.github.com/api/v3/orga/url/statuses_url')

    @patch('utils.Session', MagicMock())
    @patch('utils.get_proxy')
    def test_it_gets_patched_label_urls(self,
                                        get_proxy):
        get_proxy.return_value = 'https://ghproxy.github.com/api/v3/'
        pr = PullRequest({'pull_request': {'issue_url': 'https://api.github.com/orga/url/issueurl'}})
        self.assertEqual(pr.label_url, 'https://ghproxy.github.com/api/v3/orga/url/issueurl/labels')
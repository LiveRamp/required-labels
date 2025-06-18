import json
import logging
import time
from requests import Session
from requests.adapters import HTTPAdapter
from requests.exceptions import RequestException, Timeout, ConnectionError
from urllib3.util.retry import Retry

from exceptions import NoGitHubTokenException
from config import get_token, get_credentials, get_proxy, APP_NAME

logger = logging.getLogger(__name__)

# Configuration constants
DEFAULT_TIMEOUT = 10  # seconds
MAX_RETRIES = 3
BACKOFF_FACTOR = 0.3


def test_github_connectivity():
    """Test GitHub API connectivity"""
    try:
        session = create_github_session()
        # Test with a simple API call
        response = session.get('https://api.github.com/rate_limit', timeout=DEFAULT_TIMEOUT)
        
        if response.status_code == 200:
            rate_limit_info = response.json()
            return {
                'status': 'ok',
                'rate_limit': rate_limit_info.get('rate', {}),
                'response_time_ms': response.elapsed.total_seconds() * 1000
            }
        else:
            return {
                'status': 'error',
                'error': f'HTTP {response.status_code}: {response.text}'
            }
            
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e)
        }


def create_github_session():
    """Create a configured requests session for GitHub API calls"""
    session = Session()
    
    # Configure retry strategy
    retry_strategy = Retry(
        total=MAX_RETRIES,
        backoff_factor=BACKOFF_FACTOR,
        status_forcelist=[429, 500, 502, 503, 504],
        method_whitelist=["HEAD", "GET", "OPTIONS", "POST"]
    )
    
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    # Set authentication
    try:
        token = get_token()
        session.headers.update({"Authorization": f"token {token}"})
        logger.info("Using GitHub token authentication")
    except NoGitHubTokenException:
        credentials = get_credentials()
        if credentials:
            session.auth = credentials
            logger.info("Using GitHub username/password authentication")
        else:
            logger.warning("No GitHub authentication configured")
    
    # Set headers
    session.headers.update({"User-Agent": APP_NAME})
    session.headers.update({"Accept": "application/vnd.github.v3+json"})
    
    return session


class PullRequest:
    def __init__(self, event=None, request_id=None):
        self.event = event
        self.request_id = request_id or f"pr_{int(time.time())}"
        self._session = create_github_session()
        self.github_proxy = get_proxy()
        
        if event is not None:
            self.issue_url = event['pull_request']['issue_url']
            logger.info(f"[{self.request_id}] Initialized PullRequest for {self.issue_url}")

    @property
    def labels(self):
        return self.request_labels_json()

    def request_labels_json(self):
        """Request labels with comprehensive error handling and logging"""
        logger.info(f"[{self.request_id}] Requesting labels from {self.label_url}")
        
        try:
            start_time = time.time()
            response = self._session.get(self.label_url, timeout=DEFAULT_TIMEOUT)
            response_time = (time.time() - start_time) * 1000
            
            logger.info(f"[{self.request_id}] Labels API response: {response.status_code} "
                       f"(took {response_time:.2f}ms)")
            
            if response.status_code >= 300:
                logger.error(f"[{self.request_id}] Non-2xx status code: {response.status_code}")
                logger.error(f"[{self.request_id}] Response headers: {dict(response.headers)}")
                logger.error(f"[{self.request_id}] Response content: {response.text[:500]}")
                # Return empty list to prevent further errors
                return []
            
            labels_data = response.json()
            logger.info(f"[{self.request_id}] Retrieved {len(labels_data)} labels")
            return labels_data
            
        except Timeout as e:
            logger.error(f"[{self.request_id}] Timeout requesting labels: {str(e)}")
            return []
        except ConnectionError as e:
            logger.error(f"[{self.request_id}] Connection error requesting labels: {str(e)}")
            return []
        except RequestException as e:
            logger.error(f"[{self.request_id}] Request error requesting labels: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"[{self.request_id}] Unexpected error requesting labels: {str(e)}")
            return []

    @property
    def label_url(self):
        base_url = "{}/labels".format(self.issue_url)
        if self.github_proxy is not None:
            return base_url.replace("https://api.github.com/", self.github_proxy)
        return base_url

    def compute_and_post_status(self, required_any, required_all, banned, status_text, status_target_url):
        """Compute status and post with enhanced logging"""
        logger.info(f"[{self.request_id}] Computing and posting status")
        logger.info(f"[{self.request_id}] Required any: {required_any}")
        logger.info(f"[{self.request_id}] Required all: {required_all}")
        logger.info(f"[{self.request_id}] Banned: {banned}")
        
        return self.post_status(self.create_status_json(required_any, required_all, banned, status_text, status_target_url))

    def post_status(self, status_json):
        """Post status with comprehensive error handling and logging"""
        logger.info(f"[{self.request_id}] Posting status to {self.statuses_url}")
        logger.info(f"[{self.request_id}] Status payload: {status_json}")
        
        try:
            start_time = time.time()
            response = self._session.post(
                self.statuses_url, 
                data=status_json, 
                timeout=DEFAULT_TIMEOUT,
                headers={'Content-Type': 'application/json'}
            )
            response_time = (time.time() - start_time) * 1000
            
            logger.info(f"[{self.request_id}] Status API response: {response.status_code} "
                       f"(took {response_time:.2f}ms)")
            
            if response.status_code >= 300:
                logger.error(f"[{self.request_id}] Failed to post status: {response.status_code}")
                logger.error(f"[{self.request_id}] Response: {response.text[:500]}")
            else:
                logger.info(f"[{self.request_id}] Status posted successfully")
            
            return response.status_code
            
        except Timeout as e:
            logger.error(f"[{self.request_id}] Timeout posting status: {str(e)}")
            return 504  # Gateway timeout
        except ConnectionError as e:
            logger.error(f"[{self.request_id}] Connection error posting status: {str(e)}")
            return 502  # Bad gateway
        except RequestException as e:
            logger.error(f"[{self.request_id}] Request error posting status: {str(e)}")
            return 500  # Internal server error
        except Exception as e:
            logger.error(f"[{self.request_id}] Unexpected error posting status: {str(e)}")
            return 500

    @property
    def statuses_url(self):
        base_url = self.event['pull_request']['statuses_url']
        if self.github_proxy is not None:
            return base_url.replace("https://api.github.com/", self.github_proxy)
        return base_url

    def create_status_json(self, required_any, required_all, banned, status_text, status_target_url):
        """Create status JSON with enhanced logging"""
        logger.info(f"[{self.request_id}] Creating status JSON")
        
        passes_label_requirements = self.validate_labels(required_any, required_all, banned)
        
        if passes_label_requirements:
            description = "Label requirements satisfied."
            state = "success"
        else:
            description = status_text
            state = "failure"
            
        logger.info(f"[{self.request_id}] Label validation result: {passes_label_requirements}")
        logger.info(f"[{self.request_id}] Status state: {state}")
        
        response_json = {
            "state": state,
            "target_url": status_target_url,
            "description": description,
            "context": APP_NAME,
        }
        
        return json.dumps(response_json)

    def validate_labels(self, required_any, required_all, banned):
        """Validate labels with enhanced logging and error handling"""
        logger.info(f"[{self.request_id}] Validating labels")
        
        try:
            labels_json = self.labels
            if not isinstance(labels_json, list):
                logger.error(f"[{self.request_id}] Labels data is not a list: {type(labels_json)}")
                return False
                
            labels_list = [l.get('name', '') for l in labels_json if isinstance(l, dict)]
            logger.info(f"[{self.request_id}] Current labels: {labels_list}")
            
            # Check required_any
            if required_any is not None:
                has_required_any = any(l in required_any for l in labels_list)
                logger.info(f"[{self.request_id}] Required any check: {has_required_any} "
                           f"(need one of: {required_any})")
                if not has_required_any:
                    return False
            
            # Check required_all
            if required_all is not None:
                missing_required = [l for l in required_all if l not in labels_list]
                logger.info(f"[{self.request_id}] Required all check - missing: {missing_required}")
                if missing_required:
                    return False
            
            # Check banned
            if banned is not None:
                found_banned = [l for l in labels_list if l in banned]
                logger.info(f"[{self.request_id}] Banned labels check - found: {found_banned}")
                if found_banned:
                    return False
            
            logger.info(f"[{self.request_id}] All label validations passed")
            return True
            
        except Exception as e:
            logger.error(f"[{self.request_id}] Error validating labels: {str(e)}")
            logger.error(f"[{self.request_id}] Labels data: {labels_json if 'labels_json' in locals() else 'Not retrieved'}")
            return False

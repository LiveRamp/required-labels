import os
import logging
import traceback
from datetime import datetime

from flask import Flask, request, jsonify

from utils import PullRequest
from config import CONFIG

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('webhook.log') if not os.environ.get('DYNO') else logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)


@app.route('/', methods=["POST"])
def main():
    start_time = datetime.now()
    request_id = f"req_{int(start_time.timestamp())}"
    
    logger.info(f"[{request_id}] Webhook request received")
    logger.info(f"[{request_id}] Request headers: {dict(request.headers)}")
    
    try:
        event_json = request.get_json()
        if not event_json:
            logger.warning(f"[{request_id}] No JSON payload received")
            return jsonify({'error': 'No JSON payload'}), 400
            
        logger.info(f"[{request_id}] Event action: {event_json.get('action', 'unknown')}")
        
        if event_warrants_label_check(event_json):
            logger.info(f"[{request_id}] Event warrants label check")
            
            pull_request = PullRequest(event_json, request_id)
            logger.info(f"[{request_id}] Checking labels for PR {pull_request.issue_url}")
            
            status_code = pull_request.compute_and_post_status(
                CONFIG['required_any'],
                CONFIG['required_all'],
                CONFIG['banned'],
                CONFIG['github_status_text'],
                CONFIG['github_status_url'],
                required_env=CONFIG['required_env'],
            )
            
            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"[{request_id}] Request completed in {duration:.2f}s with status {status_code}")
            
            return jsonify({
                'status': 'success',
                'status_code': status_code,
                'duration': duration,
                'request_id': request_id
            }), 200
        else:
            logger.info(f"[{request_id}] No label check needed for action: {event_json.get('action', 'unknown')}")
            return jsonify({
                'status': 'skipped',
                'message': 'No label check needed',
                'request_id': request_id
            }), 200
            
    except Exception as e:
        duration = (datetime.now() - start_time).total_seconds()
        logger.error(f"[{request_id}] Error processing webhook after {duration:.2f}s: {str(e)}")
        logger.error(f"[{request_id}] Traceback: {traceback.format_exc()}")
        
        return jsonify({
            'error': 'Internal server error',
            'message': str(e),
            'request_id': request_id,
            'duration': duration
        }), 500


@app.route('/health', methods=["GET"])
def health():
    """Enhanced health check endpoint"""
    start_time = datetime.now()
    health_data = {
        'status': 'healthy',
        'service': 'required-labels',
        'timestamp': start_time.isoformat(),
        'version': '1.0.0',
        'uptime': 'unknown'
    }
    
    try:
        # Test GitHub API connectivity
        from utils import test_github_connectivity
        github_status = test_github_connectivity()
        health_data['github_api'] = github_status
        
        # Test configuration
        config_status = test_configuration()
        health_data['configuration'] = config_status
        
        # Overall health
        overall_healthy = github_status['status'] == 'ok' and config_status['status'] == 'ok'
        health_data['status'] = 'healthy' if overall_healthy else 'degraded'
        
        status_code = 200 if overall_healthy else 503
        
        logger.info(f"Health check completed: {health_data}")
        return jsonify(health_data), status_code
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        health_data.update({
            'status': 'unhealthy',
            'error': str(e)
        })
        return jsonify(health_data), 503


@app.route('/config', methods=["GET"])
def config():
    """Configuration endpoint with enhanced logging"""
    logger.info("Configuration endpoint accessed")
    
    try:
        config_info = {
            'required_any': CONFIG.get('required_any', []),
            'required_all': CONFIG.get('required_all', []),
            'banned': CONFIG.get('banned', []),
            'required_env': CONFIG.get('required_env', []),
            'github_status_text': CONFIG.get('github_status_text', ''),
            'github_user_configured': bool(CONFIG.get('github_user')),
            'github_token_configured': bool(CONFIG.get('github_token')),
            'github_proxy_configured': bool(CONFIG.get('github_proxy'))
        }
        
        return jsonify(config_info), 200
        
    except Exception as e:
        logger.error(f"Error accessing configuration: {str(e)}")
        return jsonify({'error': 'Configuration error'}), 500


def test_configuration():
    """Test if configuration is valid"""
    try:
        issues = []
        
        # Check label configuration
        if not any([CONFIG.get('required_any'), CONFIG.get('required_all'), CONFIG.get('banned'), CONFIG.get('required_env')]):
            issues.append("No label requirements configured")
            
        # Check GitHub credentials
        if not CONFIG.get('github_token') and not (CONFIG.get('github_user') and CONFIG.get('github_pw')):
            issues.append("No GitHub credentials configured")
            
        return {
            'status': 'ok' if not issues else 'error',
            'issues': issues
        }
    except Exception as e:
        return {
            'status': 'error',
            'issues': [f"Configuration test failed: {str(e)}"]
        }


def event_warrants_label_check(pr_event_json):
    """Check if event warrants label validation with enhanced logging"""
    try:
        action = pr_event_json.get('action')
        valid_actions = ['opened', 'reopened', 'labeled', 'unlabeled', 'synchronize']
        warrants_check = action in valid_actions
        
        logger.info(f"Event action '{action}' warrants check: {warrants_check}")
        return warrants_check
        
    except Exception as e:
        logger.error(f"Error checking if event warrants label check: {str(e)}")
        return False


# Add request logging middleware
@app.before_request
def log_request_info():
    logger.info(f"Request: {request.method} {request.url}")
    logger.info(f"Remote addr: {request.remote_addr}")
    logger.info(f"User agent: {request.headers.get('User-Agent', 'Unknown')}")


@app.after_request
def log_response_info(response):
    logger.info(f"Response: {response.status_code}")
    return response


if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"Starting application on port {port}")
    logger.info(f"Configuration: {test_configuration()}")
    app.run(host='0.0.0.0', port=port, debug=False)

# Enhanced Webhook Deployment Guide

## What's Fixed

The webhook has been enhanced to fix the 504 timeout issues:

1. **Added Comprehensive Logging**: All requests now have detailed logging with request IDs for easy tracking
2. **Added Timeout Handling**: HTTP requests now have 10-second timeouts to prevent hanging
3. **Added Retry Logic**: Automatic retry for failed requests with exponential backoff
4. **Enhanced Error Handling**: Better error handling and reporting for debugging
5. **Improved Health Check**: More detailed health check with GitHub API connectivity test
6. **Request Tracking**: Each request gets a unique ID for easier debugging

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
Create a `custom.conf` file or set environment variables:

**Option A: Configuration File**
```bash
cp custom.conf.template custom.conf
# Edit custom.conf with your GitHub credentials and label requirements
```

**Option B: Environment Variables**
```bash
export GITHUB_TOKEN="your_github_token"
export REQUIRED_LABELS_ANY="bug,feature,enhancement"
export REQUIRED_LABELS_ALL="reviewed"
export BANNED_LABELS="wip,draft"
```

### 3. Run the Application
```bash
# For development
python main.py

# For production with gunicorn
gunicorn main:app --bind 0.0.0.0:5000 --timeout 30 --workers 2
```

## Testing

### 1. Test Locally
```bash
# Test with the provided test script
python test_webhook.py

# Or test a specific URL
python test_webhook.py http://your-app-url.com
```

### 2. Check Health Status
```bash
curl http://localhost:5000/health
```

### 3. View Configuration
```bash
curl http://localhost:5000/config
```

### 4. Test Webhook Manually
```bash
curl -X POST http://localhost:5000/ \
  -H "Content-Type: application/json" \
  -d '{
    "action": "opened",
    "pull_request": {
      "issue_url": "https://api.github.com/repos/owner/repo/issues/123",
      "statuses_url": "https://api.github.com/repos/owner/repo/statuses/abc123"
    }
  }'
```

## Monitoring and Debugging

### 1. Check Logs
Logs are written to stdout and to `webhook.log` (if not on Heroku):
```bash
tail -f webhook.log
```

### 2. Key Log Patterns
- `[req_XXXXXX]` - Each request has a unique ID
- `Response Time: XXXms` - Monitor response times
- `Status API response: XXX` - GitHub API call results
- `Label validation result: True/False` - Label check outcomes

### 3. Common Issues and Solutions

**504 Gateway Timeout**
- Check if GitHub API is accessible
- Verify GitHub token has proper permissions
- Look for timeout errors in logs

**Authentication Issues**
- Verify GITHUB_TOKEN is set correctly
- Check token permissions (needs repo status access)
- Test with /health endpoint

**Configuration Issues**
- Use /config endpoint to verify settings
- Check label requirements are properly formatted
- Verify required environment variables are set

## Production Deployment

### Heroku
```bash
# Set environment variables
heroku config:set GITHUB_TOKEN=your_token
heroku config:set REQUIRED_LABELS_ANY=bug,feature

# Deploy
git push heroku main
```

### Docker
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["gunicorn", "main:app", "--bind", "0.0.0.0:5000", "--timeout", "30"]
```

## Performance Optimizations

1. **Timeout Settings**: Requests timeout after 10 seconds
2. **Retry Logic**: Up to 3 retries with exponential backoff
3. **Connection Pooling**: Reuses HTTP connections
4. **Error Handling**: Graceful degradation on failures

## Troubleshooting

### Enable Debug Logging
```python
import logging
logging.getLogger().setLevel(logging.DEBUG)
```

### Test GitHub Connectivity
```bash
curl -H "Authorization: token YOUR_TOKEN" https://api.github.com/rate_limit
```

### Check GitHub Webhook Delivery
1. Go to your GitHub repo settings
2. Navigate to Webhooks
3. Check the "Recent Deliveries" section
4. Look for failed deliveries and error messages

## Configuration Examples

### Basic Label Requirements
```bash
REQUIRED_LABELS_ANY="bug,feature,enhancement"  # At least one required
REQUIRED_LABELS_ALL="reviewed,tested"          # All required
BANNED_LABELS="wip,draft,do-not-merge"         # None allowed
```

### GitHub Status Configuration
```bash
GITHUB_STATUS_TEXT="Please add required labels"
GITHUB_STATUS_URL="https://your-docs.com/labeling-guide"
```

## Support

If you're still experiencing 504 errors:

1. Check the logs for specific error messages
2. Test the /health endpoint to verify GitHub connectivity
3. Run the test script to identify slow endpoints
4. Verify your GitHub token has the necessary permissions
5. Check if your deployment platform has timeout limits

The enhanced logging will help identify exactly where the timeouts are occurring. 
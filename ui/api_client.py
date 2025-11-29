"""
VerityNgn API Client

HTTP client for communicating with the VerityNgn API backend.
Supports local, containerized, and cloud-deployed APIs.

Usage:
    client = VerityNgnAPIClient()
    task_id = client.submit_verification(video_url)
    status = client.get_status(task_id)
    report = client.get_report(video_id, format='html')
"""

import os
import time
import requests
from typing import Dict, Any, Optional, List, Tuple
from urllib.parse import urljoin
import logging

logger = logging.getLogger(__name__)


class VerityNgnAPIClient:
    """Client for interacting with VerityNgn API backend."""
    
    def __init__(self, api_url: Optional[str] = None, timeout: int = 300):
        """
        Initialize API client.
        
        Args:
            api_url: Base URL of the API (e.g., 'http://localhost:8080' or Cloud Run URL)
                     If None, uses CLOUDRUN_API_URL or VERITYNGN_API_URL environment variable
                     or defaults to http://localhost:8080
            timeout: Request timeout in seconds (default: 300)
        """
        # Check for Cloud Run URL first, then fallback to VERITYNGN_API_URL
        self.api_url = api_url or os.getenv('CLOUDRUN_API_URL') or os.getenv('VERITYNGN_API_URL', 'http://localhost:8080')
        self.timeout = timeout
        
        # Ensure no trailing slash
        self.api_url = self.api_url.rstrip('/')
        print(f"🔍 DEBUG: API Client initialized with URL: {self.api_url}")
        
        logger.info(f"🌐 API Client initialized with URL: {self.api_url}")
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """
        Make HTTP request to API.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path (will be joined with base URL)
            **kwargs: Additional arguments to pass to requests
            
        Returns:
            requests.Response object
            
        Raises:
            requests.RequestException: On connection or HTTP errors
        """
        url = urljoin(self.api_url + '/', endpoint.lstrip('/'))
        
        try:
            response = requests.request(
                method=method,
                url=url,
                timeout=kwargs.pop('timeout', self.timeout),
                **kwargs
            )
            response.raise_for_status()
            return response
        except requests.exceptions.ConnectionError as e:
            logger.error(f"❌ Connection error to {url}: {e}")
            raise ConnectionError(
                f"Cannot connect to API at {self.api_url}. "
                f"Is the API server running? Start it with: python -m verityngn.api"
            )
        except requests.exceptions.Timeout as e:
            logger.error(f"⏱️ Request timeout to {url}: {e}")
            raise TimeoutError(f"Request to {url} timed out after {self.timeout}s")
        except requests.exceptions.HTTPError as e:
            logger.error(f"❌ HTTP error {response.status_code} from {url}: {e}")
            raise
    
    def health_check(self) -> Tuple[bool, str]:
        """
        Check if API is healthy and responsive.
        
        For Cloud Run services, allows extra time for cold starts (up to 30 seconds).
        Uses shorter timeout for local APIs (5 seconds).
        
        Returns:
            Tuple of (is_healthy, message)
        """
        import time
        
        # Determine timeout based on API URL
        # Cloud Run URLs need longer timeout for cold starts
        is_cloud_run = 'run.app' in self.api_url or 'a.run.app' in self.api_url
        initial_timeout = 30 if is_cloud_run else 5
        
        # Try with initial timeout
        try:
            response = self._make_request('GET', '/health', timeout=initial_timeout)
            data = response.json()
            return True, data.get('status', 'OK')
        except (TimeoutError, requests.exceptions.Timeout) as e:
            # If Cloud Run times out, it might be cold starting - try once more with longer timeout
            if is_cloud_run:
                logger.warning(f"⚠️ Initial health check timed out (cold start?), retrying with longer timeout...")
                try:
                    time.sleep(2)  # Brief pause before retry
                    response = self._make_request('GET', '/health', timeout=60)
                    data = response.json()
                    return True, data.get('status', 'OK')
                except Exception as retry_error:
                    return False, f"Health check failed after retry: {retry_error}"
            return False, f"Health check timeout: {e}"
        except Exception as e:
            return False, str(e)
    
    def submit_verification(self, video_url: str, config: Optional[Dict[str, Any]] = None) -> str:
        """
        Submit a video for verification.
        
        Args:
            video_url: YouTube video URL
            config: Optional configuration overrides
                    {
                        'model_name': 'gemini-2.0-flash-exp',
                        'max_claims': 20,
                        'temperature': 0.7,
                        'enable_llm_logging': True,
                        'output_formats': ['html', 'json', 'md']
                    }
        
        Returns:
            task_id: Unique task identifier for tracking
            
        Raises:
            ValueError: If video_url is invalid
            requests.RequestException: On API errors
        """
        if not video_url or not video_url.strip():
            raise ValueError("video_url cannot be empty")
        
        payload = {
            'video_url': video_url.strip(),
            'config': config or {}
        }
        
        logger.info(f"📤 Submitting verification for: {video_url}")
        
        try:
            response = self._make_request(
                'POST',
                '/api/v1/verification/verify',
                json=payload
            )
            data = response.json()
            task_id = data.get('task_id')
            
            if not task_id:
                raise ValueError("API did not return a task_id")
            
            logger.info(f"✅ Task submitted successfully: {task_id}")
            return task_id
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"❌ Failed to submit verification: {e}")
            if e.response is not None:
                try:
                    error_detail = e.response.json().get('detail', str(e))
                    raise ValueError(f"API Error: {error_detail}")
                except:
                    pass
            raise
    
    def get_status(self, task_id: str) -> Dict[str, Any]:
        """
        Get verification task status.
        
        Args:
            task_id: Task identifier from submit_verification()
        
        Returns:
            Status dictionary:
            {
                'task_id': str,
                'status': 'pending'|'processing'|'completed'|'error',
                'progress': float (0-100),
                'current_stage': str,
                'video_id': str (if available),
                'error_message': str (if error),
                'estimated_completion': str (if available)
            }
        """
        logger.debug(f"📊 Checking status for task: {task_id}")
        
        response = self._make_request(
            'GET',
            f'/api/v1/verification/status/{task_id}'
        )
        return response.json()
    
    def get_report(
        self,
        video_id: str,
        format: str = 'html'
    ) -> str:
        """
        Get verification report.
        
        Args:
            video_id: YouTube video ID
            format: Report format ('html', 'json', 'md')
        
        Returns:
            Report content as string
        """
        valid_formats = ['html', 'json', 'md']
        if format not in valid_formats:
            raise ValueError(f"format must be one of {valid_formats}")
        
        logger.info(f"📄 Fetching {format} report for video: {video_id}")
        
        response = self._make_request(
            'GET',
            f'/api/v1/reports/{video_id}/report.{format}'
        )
        
        return response.text
    
    def get_report_data(self, video_id: str) -> Dict[str, Any]:
        """
        Get report as JSON data structure.
        
        Args:
            video_id: YouTube video ID
        
        Returns:
            Report data dictionary
        """
        logger.info(f"📊 Fetching report data for video: {video_id}")
        
        response = self._make_request(
            'GET',
            f'/api/v1/reports/{video_id}/report.json'
        )
        
        return response.json()
    
    def list_reports(self) -> List[Dict[str, Any]]:
        """
        List all available reports.
        
        Returns:
            List of report metadata dictionaries
        """
        logger.info("📋 Listing available reports")
        
        response = self._make_request(
            'GET',
            '/api/v1/reports/list'
        )
        
        return response.json()
    
    def submit_batch_job(
        self,
        video_urls: List[str],
        parallelism: int = 1
    ) -> str:
        """
        Submit a batch job for processing multiple videos.
        
        Args:
            video_urls: List of YouTube video URLs
            parallelism: Number of parallel tasks (default: 1)
        
        Returns:
            job_id: Batch job identifier for tracking
            
        Raises:
            ValueError: If video_urls is empty
            requests.RequestException: On API errors
        """
        if not video_urls or len(video_urls) == 0:
            raise ValueError("video_urls cannot be empty")
        
        payload = {
            'video_urls': video_urls,
            'parallelism': parallelism
        }
        
        logger.info(f"📤 Submitting batch job for {len(video_urls)} videos")
        
        try:
            response = self._make_request(
                'POST',
                '/api/v1/batch/submit',
                json=payload
            )
            data = response.json()
            job_id = data.get('job_id')
            
            if not job_id:
                raise ValueError("API did not return a job_id")
            
            logger.info(f"✅ Batch job submitted successfully: {job_id}")
            return job_id
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"❌ Failed to submit batch job: {e}")
            if e.response is not None:
                try:
                    error_detail = e.response.json().get('detail', str(e))
                    raise ValueError(f"API Error: {error_detail}")
                except:
                    pass
            raise
    
    def get_batch_status(self, job_id: str) -> Dict[str, Any]:
        """
        Get batch job status.
        
        Args:
            job_id: Batch job identifier from submit_batch_job()
        
        Returns:
            Status dictionary:
            {
                'job_id': str,
                'status': 'running'|'completed'|'failed',
                'total_count': int,
                'completed_count': int,
                'failed_count': int,
                'completed_videos': List[str],
                'failed_videos': List[str],
                'gcs_path': str (if completed)
            }
        """
        logger.debug(f"📊 Checking batch job status: {job_id}")
        
        response = self._make_request(
            'GET',
            f'/api/v1/batch/status/{job_id}'
        )
        return response.json()
    
    def get_batch_results(self, job_id: str) -> Dict[str, Any]:
        """
        Get batch job results.
        
        Args:
            job_id: Batch job identifier
        
        Returns:
            Results dictionary with report paths and metadata
        """
        logger.info(f"📄 Fetching batch results for job: {job_id}")
        
        response = self._make_request(
            'GET',
            f'/api/v1/batch/results/{job_id}'
        )
        
        return response.json()
    
    def poll_until_complete(
        self,
        task_id: str,
        poll_interval: int = 5,
        max_wait: int = 3600,
        callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        Poll task status until completion or timeout.
        
        Args:
            task_id: Task identifier
            poll_interval: Seconds between status checks (default: 5)
            max_wait: Maximum seconds to wait (default: 3600 = 1 hour)
            callback: Optional function called on each status update
                      Signature: callback(status_dict) -> None
        
        Returns:
            Final status dictionary
            
        Raises:
            TimeoutError: If max_wait exceeded
            ValueError: If task ends in error state
        """
        logger.info(f"⏳ Polling task {task_id} until complete (max {max_wait}s)")
        
        start_time = time.time()
        
        while True:
            elapsed = time.time() - start_time
            
            if elapsed > max_wait:
                raise TimeoutError(
                    f"Task {task_id} did not complete within {max_wait}s"
                )
            
            status = self.get_status(task_id)
            
            if callback:
                try:
                    callback(status)
                except Exception as e:
                    logger.warning(f"⚠️ Callback error: {e}")
            
            task_status = status.get('status', '').lower()
            
            if task_status == 'completed':
                logger.info(f"✅ Task {task_id} completed successfully")
                return status
            
            elif task_status == 'error':
                error_msg = status.get('error_message', 'Unknown error')
                logger.error(f"❌ Task {task_id} failed: {error_msg}")
                raise ValueError(f"Task failed: {error_msg}")
            
            elif task_status in ['pending', 'processing']:
                logger.debug(
                    f"⏳ Task {task_id} {task_status} "
                    f"({status.get('progress', 0):.1f}%)"
                )
                time.sleep(poll_interval)
            
            else:
                logger.warning(f"⚠️ Unknown task status: {task_status}")
                time.sleep(poll_interval)

    def get_gallery_list(self, limit: int = 50, offset: int = 0) -> Dict[str, Any]:
        """
        Get list of gallery videos from GCS.
        
        Args:
            limit: Maximum number of videos to return (default: 50)
            offset: Number of videos to skip (default: 0)
        
        Returns:
            Gallery data dictionary:
            {
                'videos': List[Dict],
                'total': int,
                'limit': int,
                'offset': int
            }
        """
        logger.info(f"📋 Fetching gallery list (limit={limit}, offset={offset})")
        
        response = self._make_request(
            'GET',
            f'/api/v1/batch/gallery/list?limit={limit}&offset={offset}'
        )
        
        return response.json()

    def get_gallery_video(self, video_id: str) -> Dict[str, Any]:
        """
        Get specific gallery video details.
        
        Args:
            video_id: YouTube video ID
        
        Returns:
            Video metadata dictionary with signed URLs
        """
        logger.info(f"📄 Fetching gallery video: {video_id}")
        
        response = self._make_request(
            'GET',
            f'/api/v1/batch/gallery/{video_id}'
        )
        
        return response.json()


def get_default_client() -> VerityNgnAPIClient:
    """
    Get default API client instance.
    
    Convenience function for creating a client with default settings.
    
    Returns:
        VerityNgnAPIClient instance
    """
    return VerityNgnAPIClient()


# Example usage
if __name__ == "__main__":
    # Enable debug logging
    logging.basicConfig(level=logging.INFO)
    
    # Create client
    client = VerityNgnAPIClient()
    
    # Check health
    is_healthy, msg = client.health_check()
    print(f"API Health: {'✅ Healthy' if is_healthy else '❌ Unhealthy'} - {msg}")
    
    if is_healthy:
        # Example: Submit and poll
        video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        
        task_id = client.submit_verification(video_url)
        print(f"Task ID: {task_id}")
        
        def print_progress(status):
            print(f"Progress: {status.get('progress', 0):.1f}% - {status.get('current_stage', 'Unknown')}")
        
        try:
            final_status = client.poll_until_complete(
                task_id,
                poll_interval=5,
                callback=print_progress
            )
            
            video_id = final_status.get('video_id')
            if video_id:
                report = client.get_report(video_id, format='html')
                print(f"Report length: {len(report)} characters")
        
        except (TimeoutError, ValueError) as e:
            print(f"Error: {e}")





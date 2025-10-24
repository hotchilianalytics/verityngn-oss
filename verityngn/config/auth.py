"""
VerityNgn Authentication Module

Supports multiple GCP authentication methods for flexibility:
1. Service Account (JSON key file) - For local development and CI/CD
2. Application Default Credentials (ADC) - For Cloud environments
3. Workload Identity - For Kubernetes deployments

This allows the system to work in various environments without code changes.
"""

import logging
import os
from typing import Optional
from google.auth import default
from google.oauth2 import service_account
from google.auth.credentials import Credentials

logger = logging.getLogger(__name__)


class AuthProvider:
    """
    Flexible authentication provider for Google Cloud Platform.
    
    Supports three authentication methods:
    - Service Account: Uses JSON key file
    - ADC (Application Default Credentials): Uses gcloud auth
    - Workload Identity: Uses Kubernetes service account
    
    Example:
        >>> from verityngn.config.auth import AuthProvider
        >>> 
        >>> # Method 1: Service Account
        >>> config = {'method': 'service_account', 'service_account_path': 'key.json'}
        >>> auth = AuthProvider(config)
        >>> credentials = auth.get_credentials()
        >>> 
        >>> # Method 2: ADC (no config needed)
        >>> config = {'method': 'adc'}
        >>> auth = AuthProvider(config)
        >>> credentials = auth.get_credentials()
    """
    
    def __init__(self, config: Optional[dict] = None):
        """
        Initialize authentication provider.
        
        Args:
            config: Configuration dictionary with:
                - method: 'service_account', 'adc', or 'workload_identity'
                - service_account_path: Path to JSON key file (if method='service_account')
                - project_id: Optional project ID override
        """
        self.config = config or {}
        self.method = self.config.get('method', 'adc')
        self.service_account_path = self.config.get('service_account_path')
        self.project_id = self.config.get('project_id')
        self._credentials = None
        self._project_id = None
        
        logger.info(f"🔐 Initializing authentication with method: {self.method}")
    
    def get_credentials(self) -> Credentials:
        """
        Get Google Cloud credentials based on configured method.
        
        Returns:
            Google Auth credentials object
            
        Raises:
            ValueError: If authentication method is invalid
            FileNotFoundError: If service account file not found
            Exception: If authentication fails
        """
        if self._credentials:
            logger.debug("Using cached credentials")
            return self._credentials
        
        try:
            if self.method == 'service_account':
                self._credentials = self._load_service_account()
            elif self.method == 'adc':
                self._credentials = self._load_adc()
            elif self.method == 'workload_identity':
                self._credentials = self._load_workload_identity()
            else:
                raise ValueError(f"Invalid authentication method: {self.method}")
            
            logger.info(f"✅ Authentication successful using method: {self.method}")
            return self._credentials
            
        except Exception as e:
            logger.error(f"❌ Authentication failed: {e}")
            raise
    
    def _load_service_account(self) -> Credentials:
        """
        Load credentials from service account JSON key file.
        
        Returns:
            Service account credentials
            
        Raises:
            FileNotFoundError: If key file doesn't exist
            ValueError: If key file path not provided
        """
        if not self.service_account_path:
            raise ValueError("service_account_path is required for service_account method")
        
        # Expand environment variables and user home directory
        key_path = os.path.expandvars(os.path.expanduser(self.service_account_path))
        
        if not os.path.exists(key_path):
            raise FileNotFoundError(f"Service account key file not found: {key_path}")
        
        logger.info(f"📄 Loading service account from: {key_path}")
        
        credentials = service_account.Credentials.from_service_account_file(
            key_path,
            scopes=[
                'https://www.googleapis.com/auth/cloud-platform',
                'https://www.googleapis.com/auth/drive.readonly'
            ]
        )
        
        # Extract project ID from service account file if not provided
        if not self._project_id:
            import json
            with open(key_path, 'r') as f:
                key_data = json.load(f)
                self._project_id = key_data.get('project_id')
        
        return credentials
    
    def _load_adc(self) -> Credentials:
        """
        Load Application Default Credentials (ADC).
        
        ADC looks for credentials in the following order:
        1. GOOGLE_APPLICATION_CREDENTIALS environment variable
        2. gcloud auth application-default login
        3. Compute Engine/Cloud Run metadata service
        
        Returns:
            ADC credentials
            
        Raises:
            Exception: If ADC cannot be loaded
        """
        logger.info("🔍 Loading Application Default Credentials (ADC)")
        
        credentials, project = default(
            scopes=[
                'https://www.googleapis.com/auth/cloud-platform',
                'https://www.googleapis.com/auth/drive.readonly'
            ]
        )
        
        self._project_id = project or self.project_id
        
        logger.info(f"✅ ADC loaded successfully for project: {self._project_id}")
        
        return credentials
    
    def _load_workload_identity(self) -> Credentials:
        """
        Load Workload Identity credentials (for Kubernetes).
        
        Workload Identity allows Kubernetes service accounts to act as
        Google service accounts without managing keys.
        
        Returns:
            Workload Identity credentials
            
        Raises:
            Exception: If Workload Identity cannot be loaded
        """
        logger.info("🔍 Loading Workload Identity credentials")
        
        # Workload Identity uses ADC under the hood
        credentials, project = default(
            scopes=[
                'https://www.googleapis.com/auth/cloud-platform',
                'https://www.googleapis.com/auth/drive.readonly'
            ]
        )
        
        self._project_id = project or self.project_id
        
        logger.info(f"✅ Workload Identity loaded successfully for project: {self._project_id}")
        
        return credentials
    
    def get_project_id(self) -> Optional[str]:
        """
        Get the GCP project ID.
        
        Returns:
            Project ID string or None if not available
        """
        if not self._project_id and not self._credentials:
            # Try to get credentials to populate project_id
            self.get_credentials()
        
        return self._project_id or self.project_id
    
    def validate(self) -> bool:
        """
        Validate that credentials work by making a test API call.
        
        Returns:
            True if credentials are valid, False otherwise
        """
        try:
            from google.cloud import storage
            
            credentials = self.get_credentials()
            client = storage.Client(
                credentials=credentials,
                project=self.get_project_id()
            )
            
            # Test by listing buckets (requires minimal permissions)
            list(client.list_buckets(max_results=1))
            
            logger.info("✅ Credentials validated successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Credential validation failed: {e}")
            return False


def get_auth_provider(config: Optional[dict] = None) -> AuthProvider:
    """
    Factory function to get an authentication provider.
    
    Args:
        config: Optional configuration dict
        
    Returns:
        Configured AuthProvider instance
        
    Example:
        >>> from verityngn.config.auth import get_auth_provider
        >>> auth = get_auth_provider({'method': 'adc'})
        >>> credentials = auth.get_credentials()
    """
    return AuthProvider(config)


def auto_detect_auth() -> AuthProvider:
    """
    Auto-detect the best authentication method based on environment.
    
    Detection order:
    1. GOOGLE_APPLICATION_CREDENTIALS env var → service_account
    2. In Cloud Run/GCE → adc
    3. Local gcloud auth → adc
    
    Returns:
        AuthProvider with auto-detected configuration
    """
    logger.info("🔍 Auto-detecting authentication method...")
    
    # Check for service account file
    if 'GOOGLE_APPLICATION_CREDENTIALS' in os.environ:
        logger.info("Found GOOGLE_APPLICATION_CREDENTIALS, using service account")
        return AuthProvider({
            'method': 'service_account',
            'service_account_path': os.environ['GOOGLE_APPLICATION_CREDENTIALS']
        })
    
    # Check if running in Cloud environment
    if os.path.exists('/var/run/secrets/kubernetes.io/serviceaccount'):
        logger.info("Running in Kubernetes, using workload identity")
        return AuthProvider({'method': 'workload_identity'})
    
    # Default to ADC (works with gcloud auth)
    logger.info("Using Application Default Credentials (ADC)")
    return AuthProvider({'method': 'adc'})



"""
VerityNgn Configuration Loader

Loads configuration from YAML file and merges with environment variables.
Provides a clean interface to access all configuration settings.

Priority order (highest to lowest):
1. Environment variables
2. config.yaml file
3. config.yaml.example (fallback)
4. Hardcoded defaults
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional
import yaml

logger = logging.getLogger(__name__)


class ConfigLoader:
    """
    Load and manage VerityNgn configuration.
    
    Example:
        >>> from verityngn.config.config_loader import ConfigLoader
        >>> config = ConfigLoader()
        >>> project_id = config.get('gcp.project_id')
        >>> model_name = config.get('models.vertex.model_name')
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration loader.
        
        Args:
            config_path: Optional path to config.yaml file.
                        If not provided, searches in standard locations.
        """
        self.config = {}
        self.config_path = self._find_config_file(config_path)
        self._load_config()
        self._merge_env_vars()
        
        logger.info(f"✅ Configuration loaded from: {self.config_path}")
    
    def _find_config_file(self, config_path: Optional[str] = None) -> Path:
        """
        Find configuration file in standard locations.
        
        Search order:
        1. Provided config_path
        2. ./config.yaml
        3. ~/verityngn/config.yaml
        4. ./config.yaml.example (fallback)
        
        Args:
            config_path: Optional explicit path
            
        Returns:
            Path to configuration file
        """
        if config_path:
            path = Path(config_path)
            if path.exists():
                return path
            logger.warning(f"Provided config path not found: {config_path}")
        
        # Check standard locations
        locations = [
            Path.cwd() / "config.yaml",
            Path.home() / "verityngn" / "config.yaml",
            Path(__file__).parent.parent.parent / "config.yaml",
            Path.cwd() / "config.yaml.example",
            Path(__file__).parent.parent.parent / "config.yaml.example",
        ]
        
        for location in locations:
            if location.exists():
                logger.debug(f"Found config file: {location}")
                return location
        
        logger.warning("No config file found, using defaults")
        return None
    
    def _load_config(self):
        """Load configuration from YAML file."""
        if not self.config_path or not self.config_path.exists():
            logger.warning("Using default configuration (no config file found)")
            self.config = self._get_default_config()
            return
        
        try:
            with open(self.config_path, 'r') as f:
                self.config = yaml.safe_load(f) or {}
            logger.info(f"📄 Loaded config from: {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to load config file: {e}")
            self.config = self._get_default_config()
    
    def _merge_env_vars(self):
        """
        Merge environment variables into configuration.
        
        Environment variables override config file values.
        Format: VERITYNGN_<SECTION>_<KEY> (e.g., VERITYNGN_GCP_PROJECT_ID)
        """
        env_prefix = "VERITYNGN_"
        
        for key, value in os.environ.items():
            if not key.startswith(env_prefix):
                continue
            
            # Parse key into config path
            # VERITYNGN_GCP_PROJECT_ID -> gcp.project_id
            config_key = key[len(env_prefix):].lower().replace('_', '.')
            
            # Set nested value
            self._set_nested(self.config, config_key, value)
            logger.debug(f"Override from env: {config_key} = {value}")

        # Also merge specific standard env vars without prefix if not already set
        # This helps with local .env files using standard names
        standard_map = {
            "GOOGLE_CLOUD_PROJECT": "gcp.project_id",
            "PROJECT_ID": "gcp.project_id",
            "GCP_PROJECT_ID": "gcp.project_id",
            "GCS_BUCKET_NAME": "gcp.bucket_name",
            "GOOGLE_SEARCH_API_KEY": "search.google_search_api_key",
            "YOUTUBE_API_KEY": "search.youtube_api_key",
            "CSE_ID": "search.cse_id",
            "GOOGLE_AI_STUDIO_KEY": "models.vertex.google_ai_studio_key"
        }
        for env_name, config_path in standard_map.items():
            env_val = os.getenv(env_name)
            if env_val and (not self.get(config_path) or self.get(config_path) in ("your-project-id", "your-bucket-name")):
                self._set_nested(self.config, config_path, env_val)
                logger.debug(f"Standard env override: {config_path} = {env_val}")
    
    def _set_nested(self, config: dict, key_path: str, value: Any):
        """
        Set a nested configuration value.
        
        Args:
            config: Configuration dictionary
            key_path: Dot-separated path (e.g., 'gcp.project_id')
            value: Value to set
        """
        keys = key_path.split('.')
        current = config
        
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        current[keys[-1]] = value
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get configuration value by dot-separated path.
        
        Args:
            key_path: Dot-separated path (e.g., 'gcp.project_id')
            default: Default value if key not found
            
        Returns:
            Configuration value or default
            
        Example:
            >>> config = ConfigLoader()
            >>> project_id = config.get('gcp.project_id', 'default-project')
            >>> model = config.get('models.vertex.model_name')
        """
        keys = key_path.split('.')
        current = self.config
        
        for key in keys:
            if not isinstance(current, dict) or key not in current:
                return default
            current = current[key]
        
        return current
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """
        Get entire configuration section.
        
        Args:
            section: Section name (e.g., 'gcp', 'models')
            
        Returns:
            Section dictionary or empty dict if not found
        """
        return self.config.get(section, {})
    
    def set(self, key_path: str, value: Any):
        """
        Set configuration value.
        
        Args:
            key_path: Dot-separated path
            value: Value to set
        """
        self._set_nested(self.config, key_path, value)
    
    def _get_default_config(self) -> Dict[str, Any]:
        """
        Get default configuration values.
        
        Returns:
            Dictionary with default configuration
        """
        return {
            'authentication': {
                'method': 'adc',
                'service_account_path': None
            },
            'gcp': {
                'project_id': os.getenv('GOOGLE_CLOUD_PROJECT') or os.getenv('PROJECT_ID') or os.getenv('GCP_PROJECT_ID', 'your-project-id'),
                'location': 'us-central1',
                'bucket_name': os.getenv('GCS_BUCKET_NAME', 'your-bucket-name')
            },
            'models': {
                'vertex': {
                    'model_name': 'gemini-2.5-flash',
                    'max_output_tokens': 65536,
                    'temperature': 0.1,
                    'top_p': 0.8,
                    'top_k': 10
                },
                'agent': {
                    'model_name': 'gemini-2.5-flash',
                    'max_output_tokens': 32768,
                    'temperature': 0.7
                }
            },
            'processing': {
                'segment_fps': 1.0,
                'max_video_duration': 3600,
                'video_trim_duration': 2000,
                'claims_per_minute': 1.8,
                'min_claims': 15,
                'max_claims': 40,
                'min_claim_length': 10,
                'deduplicate_claims': True
            },
            'llm_logging': {
                'enabled': True,
                'log_prompts': True,
                'log_responses': True,
                'log_tokens': True,
                'log_timing': True,
                'log_model_version': True,
                'log_parameters': True,
                'output_dir': './llm_logs',
                'format': 'json',
                'include_metadata': True
            },
            'output': {
                'local_dir': './outputs',
                'formats': ['json', 'markdown', 'html'],
                'include_metadata': True,
                'include_evidence': True,
                'include_timestamps': True,
                'include_probability_dist': True,
                'enable_gcs_upload': False,
                'use_timestamped_storage': True
            },
            'search': {
                'google_search_api_key': os.getenv('GOOGLE_SEARCH_API_KEY'),
                'cse_id': os.getenv('CSE_ID'),
                'youtube_api_key': os.getenv('YOUTUBE_API_KEY'),
                'youtube_api_fallback': False,
                'enable_counter_intel': True,
                'counter_intel_max_results': 4,
                'detect_press_releases': True,
                'press_release_penalty': 0.15
            },
            'features': {
                'enable_multimodal_analysis': True,
                'enable_transcript_extraction': True,
                'enable_ocr': True,
                'enable_scientific_weighting': True,
                'enable_validation_power': True,
                'enable_semantic_filtering': True,
                'enable_html_reports': True,
                'enable_interactive_charts': True,
                'enable_source_links': True
            },
            'performance': {
                'max_concurrent_claims': 5,
                'max_concurrent_downloads': 3,
                'video_download_timeout': 600,
                'llm_request_timeout': 120,
                'search_request_timeout': 30,
                'rate_limit_delay': 2,
                'enable_caching': True,
                'cache_ttl': 86400
            },
            'logging': {
                'level': 'INFO',
                'format': 'text',
                'output': 'stdout',
                'log_file': './logs/verityngn.log'
            },
            'advanced': {
                'deployment_mode': 'research',
                'storage_backend': 'local',
                'debug': False,
                'verbose': False,
                'save_intermediate': False
            }
        }
    
    def validate(self) -> bool:
        """
        Validate configuration for required fields.
        
        Returns:
            True if configuration is valid, False otherwise
        """
        required_fields = [
            'gcp.project_id',
            'gcp.location',
            'models.vertex.model_name'
        ]
        
        missing = []
        for field in required_fields:
            value = self.get(field)
            if not value or value == 'your-project-id' or value == 'your-bucket-name':
                missing.append(field)
        
        if missing:
            logger.error(f"❌ Missing or invalid required configuration fields: {missing}")
            logger.error("Please update your config.yaml file with valid values")
            return False
        
        logger.info("✅ Configuration validation passed")
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Get complete configuration as dictionary.
        
        Returns:
            Configuration dictionary
        """
        return self.config.copy()


# Global configuration instance
_config = None


def get_config(config_path: Optional[str] = None, reload: bool = False) -> ConfigLoader:
    """
    Get global configuration instance (singleton).
    
    Args:
        config_path: Optional path to config file
        reload: Force reload configuration
        
    Returns:
        ConfigLoader instance
    """
    global _config
    
    if _config is None or reload:
        _config = ConfigLoader(config_path)
    
    return _config



import os
import sys
from pathlib import Path

# Add project root to path
repo_root = Path(__file__).parent
sys.path.insert(0, str(repo_root))

from verityngn.config.config_loader import get_config

def test_config_env_vars():
    # Set environment variables
    os.environ["STORAGE_BACKEND"] = "gcs"
    os.environ["DEPLOYMENT_MODE"] = "production"
    os.environ["LOCATION"] = "us-east1"
    
    # Force reload config
    config = get_config(reload=True)
    
    print(f"STORAGE_BACKEND: {config.get('advanced.storage_backend')}")
    print(f"DEPLOYMENT_MODE: {config.get('advanced.deployment_mode')}")
    print(f"LOCATION: {config.get('gcp.location')}")
    
    assert config.get('advanced.storage_backend') == "gcs"
    assert config.get('advanced.deployment_mode') == "production"
    assert config.get('gcp.location') == "us-east1"
    print("\n✅ Verification SUCCESS: Standard environment variables correctly mapped!")

if __name__ == "__main__":
    test_config_env_vars()

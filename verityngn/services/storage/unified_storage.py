"""
Unified Storage Service

Provides a consistent interface for storing and retrieving files
regardless of the underlying storage backend (local filesystem or GCS).
"""

import os
import logging
import json
import zipfile
import io
from typing import List, Dict, Any, Optional, Tuple, Union
from pathlib import Path
from abc import ABC, abstractmethod

from verityngn.config.settings import STORAGE_CONFIG, STORAGE_BACKEND, StorageBackend
from verityngn.services.storage.gcs import GCSStorageService


class StorageServiceInterface(ABC):
    """Abstract interface for storage services."""
    
    @abstractmethod
    def save_file(self, content: Union[str, bytes], file_path: str) -> str:
        """Save content to a file and return the accessible path/URL."""
        pass
    
    @abstractmethod
    def read_file(self, file_path: str) -> str:
        """Read and return file content."""
        pass
    
    @abstractmethod
    def file_exists(self, file_path: str) -> bool:
        """Check if a file exists."""
        pass
    
    @abstractmethod
    def list_files(self, directory_path: str, pattern: str = "*") -> List[str]:
        """List files in a directory matching the pattern."""
        pass
    
    @abstractmethod
    def get_file_url(self, file_path: str) -> str:
        """Get a URL for accessing the file."""
        pass
    
    @abstractmethod
    def delete_file(self, file_path: str) -> bool:
        """Delete a file."""
        pass


class LocalStorageService(StorageServiceInterface):
    """Local filesystem storage implementation."""
    
    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)
    
    def _get_full_path(self, file_path: str) -> Path:
        """Convert relative file path to full local path."""
        if os.path.isabs(file_path):
            return Path(file_path)
        return self.base_dir / file_path
    
    def save_file(self, content: Union[str, bytes], file_path: str) -> str:
        """Save content to a local file."""
        full_path = self._get_full_path(file_path)
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        mode = 'w' if isinstance(content, str) else 'wb'
        encoding = 'utf-8' if isinstance(content, str) else None
        
        with open(full_path, mode, encoding=encoding) as f:
            f.write(content)
        
        self.logger.info(f"Saved file to local storage: {full_path}")
        return str(full_path)
    
    def read_file(self, file_path: str) -> str:
        """Read content from a local file."""
        full_path = self._get_full_path(file_path)
        
        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {full_path}")
        
        with open(full_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def file_exists(self, file_path: str) -> bool:
        """Check if a local file exists."""
        return self._get_full_path(file_path).exists()
    
    def list_files(self, directory_path: str, pattern: str = "*") -> List[str]:
        """List files in a local directory."""
        full_dir = self._get_full_path(directory_path)
        
        if not full_dir.exists():
            return []
        
        # Return relative paths from base directory
        files = []
        for file_path in full_dir.glob(pattern):
            if file_path.is_file():
                rel_path = file_path.relative_to(self.base_dir)
                files.append(str(rel_path))
        
        return files
    
    def get_file_url(self, file_path: str) -> str:
        """Get local file path as URL."""
        full_path = self._get_full_path(file_path)
        return f"file://{full_path}"
    
    def delete_file(self, file_path: str) -> bool:
        """Delete a local file."""
        try:
            full_path = self._get_full_path(file_path)
            if full_path.exists():
                full_path.unlink()
                self.logger.info(f"Deleted local file: {full_path}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error deleting file {file_path}: {e}")
            return False


class GCSStorageServiceAdapter(StorageServiceInterface):
    """GCS storage implementation using the existing GCSStorageService."""
    
    def __init__(self, bucket_name: str, base_path: str = ""):
        self.gcs_service = GCSStorageService(bucket_name)
        self.base_path = base_path.strip("/")
        self.bucket_name = bucket_name
        self.logger = logging.getLogger(__name__)
    
    def _get_gcs_path(self, file_path: str) -> str:
        """Convert file path to GCS path."""
        if self.base_path:
            return f"{self.base_path}/{file_path.lstrip('/')}"
        return file_path.lstrip("/")
    
    def save_file(self, content: Union[str, bytes], file_path: str) -> str:
        """Save content to GCS."""
        import tempfile
        
        gcs_path = self._get_gcs_path(file_path)
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            if isinstance(content, str):
                tmp_file.write(content.encode('utf-8'))
            else:
                tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        try:
            # Upload to GCS
            success, signed_url = self.gcs_service.upload_file(tmp_file_path, gcs_path)
            if success:
                self.logger.info(f"Saved file to GCS: gs://{self.bucket_name}/{gcs_path}")
                return signed_url or f"gs://{self.bucket_name}/{gcs_path}"
            else:
                raise Exception("Failed to upload to GCS")
        finally:
            # Clean up temporary file
            os.unlink(tmp_file_path)
    
    def read_file(self, file_path: str) -> str:
        """Read content from GCS."""
        import tempfile
        
        gcs_path = self._get_gcs_path(file_path)
        
        with tempfile.NamedTemporaryFile() as tmp_file:
            if self.gcs_service.download_file(gcs_path, tmp_file.name):
                with open(tmp_file.name, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                raise FileNotFoundError(f"File not found in GCS: gs://{self.bucket_name}/{gcs_path}")
    
    def file_exists(self, file_path: str) -> bool:
        """Check if file exists in GCS."""
        gcs_path = self._get_gcs_path(file_path)
        files = self.gcs_service.list_files(gcs_path)
        return gcs_path in files
    
    def list_files(self, directory_path: str, pattern: str = "*") -> List[str]:
        """List files in GCS with directory prefix."""
        gcs_prefix = self._get_gcs_path(directory_path)
        files = self.gcs_service.list_files(gcs_prefix)
        
        # Filter by pattern if needed (simple implementation)
        if pattern != "*":
            import fnmatch
            files = [f for f in files if fnmatch.fnmatch(f, f"{gcs_prefix}/*{pattern}")]
        
        # Return relative paths
        result = []
        for file_path in files:
            if self.base_path:
                rel_path = file_path.replace(f"{self.base_path}/", "", 1)
            else:
                rel_path = file_path
            result.append(rel_path)
        
        return result
    
    def get_file_url(self, file_path: str) -> str:
        """Get signed URL for GCS file."""
        gcs_path = self._get_gcs_path(file_path)
        
        # Generate signed URL
        try:
            from google.cloud import storage
            from datetime import timedelta
            
            client = storage.Client()
            bucket = client.bucket(self.bucket_name)
            blob = bucket.blob(gcs_path)
            
            signed_url = blob.generate_signed_url(
                version="v4",
                expiration=timedelta(days=7),
                method="GET"
            )
            return signed_url
        except Exception as e:
            self.logger.error(f"Error generating signed URL: {e}")
            return f"gs://{self.bucket_name}/{gcs_path}"
    
    def delete_file(self, file_path: str) -> bool:
        """Delete file from GCS."""
        try:
            gcs_path = self._get_gcs_path(file_path)
            from google.cloud import storage
            
            client = storage.Client()
            bucket = client.bucket(self.bucket_name)
            blob = bucket.blob(gcs_path)
            
            blob.delete()
            self.logger.info(f"Deleted GCS file: gs://{self.bucket_name}/{gcs_path}")
            return True
        except Exception as e:
            self.logger.error(f"Error deleting GCS file {file_path}: {e}")
            return False


class UnifiedStorageService:
    """Unified storage service that provides a consistent interface."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Initialize appropriate storage backend with fallback
        if STORAGE_BACKEND == StorageBackend.GCS:
            try:
                gcs_config = STORAGE_CONFIG["gcs"]
                self.storage = GCSStorageServiceAdapter(
                    bucket_name=gcs_config["bucket_name"],
                    base_path=gcs_config["base_path"]
                )
                self.logger.info("Initialized GCS storage backend")
            except Exception as e:
                self.logger.warning(f"Failed to initialize GCS storage, falling back to local: {e}")
                # Fall back to local storage
                local_config = STORAGE_CONFIG["local"]
                self.storage = LocalStorageService(local_config["downloads_dir"])
                self.logger.info(f"Initialized fallback local storage backend: {local_config['downloads_dir']}")
        else:
            local_config = STORAGE_CONFIG["local"]
            self.storage = LocalStorageService(local_config["downloads_dir"])
            self.logger.info(f"Initialized local storage backend: {local_config['downloads_dir']}")
    
    def save_report_files(self, video_id: str, files: Dict[str, str]) -> Dict[str, str]:
        """
        Save multiple report files and return their accessible URLs.
        
        Args:
            video_id: Video identifier
            files: Dict mapping filename to content
            
        Returns:
            Dict mapping filename to accessible URL
        """
        urls = {}
        
        for filename, content in files.items():
            file_path = f"{video_id}/{filename}"
            try:
                url = self.storage.save_file(content, file_path)
                urls[filename] = url
                self.logger.info(f"Saved report file: {filename}")
            except Exception as e:
                self.logger.error(f"Error saving file {filename}: {e}")
                
        return urls
    
    def get_report_file(self, video_id: str, filename: str) -> str:
        """Get content of a report file."""
        file_path = f"{video_id}/{filename}"
        return self.storage.read_file(file_path)
    
    def report_exists(self, video_id: str, filename: str) -> bool:
        """Check if a report file exists."""
        file_path = f"{video_id}/{filename}"
        return self.storage.file_exists(file_path)
    
    def list_reports(self, video_id: Optional[str] = None) -> List[str]:
        """List available reports."""
        if video_id:
            return self.storage.list_files(video_id)
        else:
            return self.storage.list_files("", "*")
    
    def get_report_url(self, video_id: str, filename: str) -> str:
        """Get URL for accessing a report file."""
        file_path = f"{video_id}/{filename}"
        return self.storage.get_file_url(file_path)
    
    def create_report_bundle(self, video_id: str, format: str = "json") -> Union[Dict[str, Any], bytes]:
        """Create a bundle of all report files for a video."""
        files = self.list_reports(video_id)
        report_files = [f for f in files if any(f.endswith(ext) for ext in ['.html', '.md', '.json']) 
                       and ('report' in f or 'claim_' in f)]
        
        if format.lower() == "json":
            bundle = {
                "video_id": video_id,
                "files": {}
            }
            
            for file_path in report_files:
                try:
                    # Extract filename from path (remove video_id prefix if present)
                    if file_path.startswith(f"{video_id}/"):
                        filename = file_path[len(f"{video_id}/"):]
                    else:
                        filename = file_path
                    
                    # Read file using the storage interface directly
                    content = self.storage.read_file(file_path)
                    
                    if filename.endswith('.json'):
                        bundle["files"][filename] = json.loads(content)
                    else:
                        bundle["files"][filename] = content
                except Exception as e:
                    self.logger.warning(f"Could not read file {file_path}: {e}")
            
            return bundle
            
        elif format.lower() == "zip":
            zip_buffer = io.BytesIO()
            
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for file_path in report_files:
                    try:
                        # Extract filename from path (remove video_id prefix if present)
                        if file_path.startswith(f"{video_id}/"):
                            filename = file_path[len(f"{video_id}/"):]
                        else:
                            filename = file_path
                        
                        # Read file using the storage interface directly
                        content = self.storage.read_file(file_path)
                        zip_file.writestr(filename, content)
                    except Exception as e:
                        self.logger.warning(f"Could not add file {file_path} to ZIP: {e}")
            
            zip_buffer.seek(0)
            return zip_buffer.getvalue()
        
        else:
            raise ValueError(f"Unsupported bundle format: {format}")

# Create singleton instance
unified_storage = UnifiedStorageService() 
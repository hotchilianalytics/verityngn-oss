import os
import logging
import glob
from typing import List, Optional, Tuple
from datetime import timedelta
from google.cloud import storage

class GCSStorageService:
    """Service for interacting with Google Cloud Storage."""
    
    def __init__(self, bucket_name: str):
        """
        Initialize the GCS storage service.
        
        Args:
            bucket_name (str): Name of the GCS bucket
        """
        self.bucket_name = bucket_name
        self.logger = logging.getLogger(__name__)
        
        # Initialize client and bucket
        try:
            self.client = storage.Client()
            # Use bucket() method instead of get_bucket() to avoid validation
            # The bucket will be validated on first upload attempt
            self.bucket = self.client.bucket(bucket_name)
            self.logger.info(f"Initialized GCS client for bucket: {bucket_name}")
        except Exception as e:
            self.logger.error(f"Error initializing GCS client for bucket {bucket_name}: {e}")
            self.client = None
            self.bucket = None
    
    def upload_file(self, local_file_path: str, gcs_path: str) -> Tuple[bool, Optional[str]]:
        """
        Upload a file to GCS and generate a signed URL.
        
        Args:
            local_file_path (str): Path to the local file
            gcs_path (str): Path in GCS to upload the file to
            
        Returns:
            Tuple[bool, Optional[str]]: (Success status, Signed URL if successful)
        """
        if not self.bucket:
            self.logger.error("Bucket not initialized")
            return False, None
        
        if not os.path.exists(local_file_path):
            self.logger.error(f"Local file not found: {local_file_path}")
            return False, None
        
        try:
            blob = self.bucket.blob(gcs_path)
            blob.upload_from_filename(local_file_path)
            
            self.logger.info(f"✅ Uploaded {local_file_path} to gs://{self.bucket_name}/{gcs_path}")
            
            # Try to generate signed URL, but don't fail if we can't
            signed_url = None
            try:
                signed_url = blob.generate_signed_url(
                    version="v4",
                    expiration=timedelta(days=7),
                    method="GET"
                )
                self.logger.info(f"Generated signed URL: {signed_url}")
            except Exception as url_error:
                self.logger.warning(f"Could not generate signed URL (upload succeeded): {url_error}")
                # Return GCS path instead
                signed_url = f"gs://{self.bucket_name}/{gcs_path}"
            
            return True, signed_url
        except Exception as e:
            self.logger.error(f"❌ Error uploading file to GCS: {e}")
            return False, None
    
    def get_signed_url(self, gcs_path: str, expiration_hours: int = 168) -> str:
        """
        Generate a signed URL for a GCS object.
        
        Args:
            gcs_path: Path in GCS (without gs://bucket/ prefix)
            expiration_hours: Hours until URL expires (default: 7 days)
            
        Returns:
            Signed URL or gs:// path if signing fails
        """
        if not self.bucket:
            self.logger.error("Bucket not initialized")
            return f"gs://{self.bucket_name}/{gcs_path}"
        
        try:
            blob = self.bucket.blob(gcs_path)
            signed_url = blob.generate_signed_url(
                version="v4",
                expiration=timedelta(hours=expiration_hours),
                method="GET"
            )
            return signed_url
        except Exception as e:
            self.logger.warning(f"Could not generate signed URL for {gcs_path}: {e}")
            # Return GCS path as fallback
            return f"gs://{self.bucket_name}/{gcs_path}"
    
    def upload_directory(self, local_dir_path: str, gcs_base_path: str, include_pattern: Optional[str] = None) -> List[str]:
        """
        Upload a directory to GCS.
        
        Args:
            local_dir_path (str): Path to the local directory
            gcs_base_path (str): Base path in GCS to upload the directory to
            include_pattern (Optional[str]): Pattern to filter files to upload
            
        Returns:
            List[str]: List of GCS paths for successfully uploaded files
        """
        if not self.bucket:
            self.logger.error("Bucket not initialized")
            return []
        
        if not os.path.exists(local_dir_path) or not os.path.isdir(local_dir_path):
            self.logger.error(f"Local directory not found: {local_dir_path}")
            return []
        
        uploaded_files = []
        
        try:
            # Get list of files to upload
            if include_pattern:
                files = glob.glob(os.path.join(local_dir_path, include_pattern))
            else:
                files = []
                for root, _, filenames in os.walk(local_dir_path):
                    for filename in filenames:
                        files.append(os.path.join(root, filename))
            
            # Upload each file
            for file_path in files:
                # Calculate relative path
                rel_path = os.path.relpath(file_path, local_dir_path)
                gcs_path = os.path.join(gcs_base_path, rel_path).replace("\\", "/")
                
                if self.upload_file(file_path, gcs_path):
                    uploaded_files.append(gcs_path)
            
            self.logger.info(f"Uploaded {len(uploaded_files)} files to gs://{self.bucket_name}/{gcs_base_path}")
            return uploaded_files
            
        except Exception as e:
            self.logger.error(f"Error uploading directory to GCS: {e}")
            return uploaded_files
    
    def download_file(self, gcs_path: str, local_file_path: str) -> bool:
        """
        Download a file from GCS.
        
        Args:
            gcs_path (str): Path in GCS to download the file from
            local_file_path (str): Path to save the local file
            
        Returns:
            bool: True if download was successful, False otherwise
        """
        if not self.bucket:
            self.logger.error("Bucket not initialized")
            return False
        
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(local_file_path), exist_ok=True)
            
            blob = self.bucket.blob(gcs_path)
            blob.download_to_filename(local_file_path)
            self.logger.info(f"Downloaded gs://{self.bucket_name}/{gcs_path} to {local_file_path}")
            return True
        except Exception as e:
            self.logger.error(f"Error downloading file from GCS: {e}")
            return False
    
    def list_files(self, gcs_path_prefix: str) -> List[str]:
        """
        List files in GCS with the given prefix.
        
        Args:
            gcs_path_prefix (str): Prefix to filter files by
            
        Returns:
            List[str]: List of GCS paths for files with the given prefix
        """
        if not self.bucket:
            self.logger.error("Bucket not initialized")
            return []
        
        try:
            blobs = self.bucket.list_blobs(prefix=gcs_path_prefix)
            return [blob.name for blob in blobs]
        except Exception as e:
            self.logger.error(f"Error listing files in GCS: {e}")
            return [] 
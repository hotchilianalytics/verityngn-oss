import logging
import os
from typing import Optional
from datetime import timedelta
from google.cloud import storage

from verityngn.config.settings import PROJECT_ID, GCS_BUCKET_NAME

def upload_to_gcs(local_file_path: str, gcs_path: str, bucket_name: Optional[str] = None) -> str:
    """
    Upload a file to Google Cloud Storage and generate a signed URL.
    
    Args:
        local_file_path (str): Path to the local file
        gcs_path (str): Path in GCS where the file should be uploaded
        bucket_name (str, optional): GCS bucket name. Defaults to GCS_BUCKET_NAME from settings.
        
    Returns:
        str: Signed URL for accessing the uploaded file
    """
    logger = logging.getLogger(__name__)
    bucket_to_use = bucket_name or GCS_BUCKET_NAME
    logger.info(f"Uploading {local_file_path} to GCS bucket '{bucket_to_use}': {gcs_path}")
    
    try:
        # Check if the file exists
        if not os.path.exists(local_file_path):
            logger.error(f"File not found: {local_file_path}")
            raise FileNotFoundError(f"File not found: {local_file_path}")
            
        # Initialize GCS client
        client = storage.Client(project=PROJECT_ID)
        
        # Get the bucket
        bucket = client.bucket(bucket_to_use)
        
        # Extract the blob name from the GCS path
        if gcs_path.startswith(f"gs://{bucket_to_use}/"):
            blob_name = gcs_path[len(f"gs://{bucket_to_use}/"):]
        else:
            blob_name = gcs_path
            
        # Create a blob
        blob = bucket.blob(blob_name)
        
        # Upload the file
        blob.upload_from_filename(local_file_path)
        
        # Generate a signed URL that expires in 7 days
        signed_url = blob.generate_signed_url(
            version="v4",
            expiration=timedelta(days=7),
            method="GET"
        )
        
        logger.info(f"File uploaded to GCS with signed URL: {signed_url}")
        return signed_url
        
    except Exception as e:
        logger.error(f"Error uploading to GCS: {e}")
        raise Exception(f"Error uploading to GCS: {e}")

def download_from_gcs(gcs_path: str, local_file_path: str) -> str:
    """
    Download a file from Google Cloud Storage.
    
    Args:
        gcs_path (str): Path in GCS where the file is stored
        local_file_path (str): Path where the file should be downloaded
        
    Returns:
        str: Path to the downloaded file
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Downloading from GCS: {gcs_path} to {local_file_path}")
    
    try:
        # Initialize GCS client
        client = storage.Client(project=PROJECT_ID)
        
        # Get the bucket
        bucket = client.bucket(GCS_BUCKET_NAME)
        
        # Extract the blob name from the GCS path
        if gcs_path.startswith(f"gs://{GCS_BUCKET_NAME}/"):
            blob_name = gcs_path[len(f"gs://{GCS_BUCKET_NAME}/"):]
        else:
            blob_name = gcs_path
            
        # Create a blob
        blob = bucket.blob(blob_name)
        
        # Download the file
        os.makedirs(os.path.dirname(local_file_path), exist_ok=True)
        blob.download_to_filename(local_file_path)
        
        logger.info(f"File downloaded from GCS: {local_file_path}")
        return local_file_path
        
    except Exception as e:
        logger.error(f"Error downloading from GCS: {e}")
        raise Exception(f"Error downloading from GCS: {e}")

def list_gcs_files(prefix: Optional[str] = None) -> list:
    """
    List files in a GCS bucket.
    
    Args:
        prefix (Optional[str]): Prefix to filter files
        
    Returns:
        list: List of file paths
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Listing GCS files with prefix: {prefix}")
    
    try:
        # Initialize GCS client
        client = storage.Client(project=PROJECT_ID)
        
        # Get the bucket
        bucket = client.bucket(GCS_BUCKET_NAME)
        
        # List blobs
        blobs = bucket.list_blobs(prefix=prefix)
        
        # Get the names
        file_paths = [f"gs://{GCS_BUCKET_NAME}/{blob.name}" for blob in blobs]
        
        logger.info(f"Found {len(file_paths)} files in GCS")
        return file_paths
        
    except Exception as e:
        logger.error(f"Error listing GCS files: {e}")
        return [] 
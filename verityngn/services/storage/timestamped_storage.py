#!/usr/bin/env python3
"""
Timestamped Storage Service
==========================

This service implements timestamped report storage with versioning and completion markers.
It ensures that only complete reports are served and provides a mechanism to find the latest version.

Key Features:
- Timestamped directories for each report generation
- Completion markers to indicate when reports are fully generated
- Latest version detection and serving
- Concurrent processing safety
- Automatic cleanup of old versions
"""

import os
import logging
import json
import shutil
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

from verityngn.config.settings import STORAGE_BACKEND, StorageBackend, STORAGE_CONFIG
from verityngn.services.storage.unified_storage import unified_storage
from verityngn.services.storage.gcs import GCSStorageService

logger = logging.getLogger(__name__)

class TimestampedStorageService:
    """
    Service for managing timestamped report storage with versioning.
    
    This service creates timestamped directories for each report generation,
    uses completion markers to ensure only complete reports are served,
    and provides mechanisms to find and serve the latest complete version.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.storage_backend = STORAGE_BACKEND
        
        if self.storage_backend == StorageBackend.GCS:
            self.gcs_service = GCSStorageService(STORAGE_CONFIG["gcs"]["bucket_name"])
        
        self.logger.info(f"Initialized timestamped storage with {self.storage_backend.value} backend")
    
    def create_timestamped_directory(self, video_id: str) -> str:
        """
        Create a new timestamped directory for report generation.
        
        Args:
            video_id: Video identifier
        
        Returns:
            str: Path to the timestamped directory. For GCS, this always includes the base path prefix (e.g. vngn_reports/...).
        """
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        
        if self.storage_backend == StorageBackend.LOCAL:
            # For local storage, create actual directory
            timestamped_dir = f"{video_id}/{timestamp}_processing"
            local_path = Path(STORAGE_CONFIG["local"]["outputs_dir"]) / timestamped_dir
            local_path.mkdir(parents=True, exist_ok=True)
            self.logger.info(f"Created local timestamped directory: {local_path}")
            return str(local_path)
        else:
            # For GCS, include the base path
            base_path = STORAGE_CONFIG["gcs"]["base_path"]
            timestamped_dir = f"{base_path}/{video_id}/{timestamp}_processing"
            self.logger.info(f"Prepared GCS timestamped directory: {timestamped_dir}")
            return timestamped_dir
    
    def mark_generation_complete(self, timestamped_dir: str, video_id: str, report_metadata: Dict[str, Any]) -> bool:
        """
        Mark a report generation as complete by creating a completion marker.
        
        Args:
            timestamped_dir: Path to the timestamped directory
            video_id: Video identifier
            report_metadata: Metadata about the generated report
            
        Returns:
            bool: True if marking was successful
        """
        try:
            # Create completion marker content
            completion_data = {
                "video_id": video_id,
                "completion_timestamp": datetime.now().isoformat(),
                "report_metadata": report_metadata,
                "files_generated": self._list_files_in_directory(timestamped_dir),
                "version": "1.0"
            }
            
            marker_content = json.dumps(completion_data, indent=2)
            
            if self.storage_backend == StorageBackend.LOCAL:
                marker_path = Path(timestamped_dir) / ".complete_marker"
                with open(marker_path, 'w') as f:
                    f.write(marker_content)
                
                # Update the directory name to indicate completion
                complete_dir = str(Path(timestamped_dir).parent / f"{Path(timestamped_dir).name.replace('_processing', '_complete')}")
                shutil.move(timestamped_dir, complete_dir)
                
                self.logger.info(f"Marked local report complete: {complete_dir}")
                return True
                
            else:
                # For GCS, upload the marker file to the same directory as the reports
                marker_path = f"{timestamped_dir}/.complete_marker"
                
                import tempfile
                with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
                    temp_file.write(marker_content)
                    temp_file_path = temp_file.name
                
                try:
                    success, _ = self.gcs_service.upload_file(temp_file_path, marker_path)
                    if success:
                        self.logger.info(f"Marked GCS report complete: {marker_path}")
                        return True
                    else:
                        self.logger.error(f"Failed to upload completion marker to GCS: {marker_path}")
                        return False
                finally:
                    os.unlink(temp_file_path)
                    
        except Exception as e:
            self.logger.error(f"Error marking generation complete: {e}")
            return False
    
    def find_latest_complete_report(self, video_id: str) -> Optional[str]:
        """
        Find the latest complete report for a video.
        
        Args:
            video_id: Video identifier
            
        Returns:
            Optional[str]: Path to the latest complete report directory, or None if none found
        """
        try:
            if self.storage_backend == StorageBackend.LOCAL:
                base_dir = Path(STORAGE_CONFIG["local"]["outputs_dir"]) / video_id
                if not base_dir.exists():
                    return None
                
                complete_dirs = []
                for item in base_dir.iterdir():
                    if item.is_dir() and item.name.endswith('_complete'):
                        marker_path = item / ".complete_marker"
                        if marker_path.exists():
                            complete_dirs.append(item)
                
                if not complete_dirs:
                    return None
                
                # Sort by timestamp (newest first)
                complete_dirs.sort(key=lambda x: x.name, reverse=True)
                latest_dir = complete_dirs[0]
                
                self.logger.info(f"Found latest local complete report: {latest_dir}")
                return str(latest_dir)
                
            else:
                # For GCS, list directories and find the latest with completion marker
                base_path = STORAGE_CONFIG["gcs"]["base_path"]
                prefix = f"{base_path}/{video_id}/"
                files = self.gcs_service.list_files(prefix)
                
                complete_dirs = set()
                for file_path in files:
                    if "/.complete_marker" in file_path:
                        dir_path = file_path.replace("/.complete_marker", "")
                        if "_processing" in dir_path:
                            complete_dirs.add(dir_path)
                
                if not complete_dirs:
                    return None
                
                # Sort by timestamp (newest first)
                sorted_dirs = sorted(complete_dirs, reverse=True)
                latest_dir = sorted_dirs[0]
                
                self.logger.info(f"Found latest GCS complete report: {latest_dir}")
                return latest_dir
                
        except Exception as e:
            self.logger.error(f"Error finding latest complete report: {e}")
            return None
    
    def get_report_file_from_timestamped_dir(self, timestamped_dir: str, filename: str) -> Optional[str]:
        """
        Get a specific report file from a timestamped directory.
        
        Args:
            timestamped_dir: Path to the timestamped directory
            filename: Name of the file to retrieve
            
        Returns:
            Optional[str]: File content, or None if not found
        """
        try:
            if self.storage_backend == StorageBackend.LOCAL:
                file_path = Path(timestamped_dir) / filename
                if file_path.exists():
                    with open(file_path, 'r', encoding='utf-8') as f:
                        return f.read()
                return None
                
            else:
                # For GCS, download the file
                file_path = f"{timestamped_dir}/{filename}"
                
                import tempfile
                with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
                    temp_file_path = temp_file.name
                
                try:
                    if self.gcs_service.download_file(file_path, temp_file_path):
                        with open(temp_file_path, 'r', encoding='utf-8') as f:
                            return f.read()
                    return None
                finally:
                    if os.path.exists(temp_file_path):
                        os.unlink(temp_file_path)
                        
        except Exception as e:
            self.logger.error(f"Error getting file from timestamped directory: {e}")
            return None
    
    def list_report_versions(self, video_id: str) -> List[Dict[str, Any]]:
        """
        List all available report versions for a video.
        
        Args:
            video_id: Video identifier
            
        Returns:
            List[Dict[str, Any]]: List of version information
        """
        try:
            versions = []
            
            if self.storage_backend == StorageBackend.LOCAL:
                base_dir = Path(STORAGE_CONFIG["local"]["outputs_dir"]) / video_id
                if not base_dir.exists():
                    return versions
                
                for item in base_dir.iterdir():
                    if item.is_dir():
                        version_info = {
                            "directory": str(item),
                            "timestamp": item.name.split('_')[0] + "_" + item.name.split('_')[1],
                            "status": "complete" if item.name.endswith('_complete') else "processing",
                            "has_completion_marker": (item / ".complete_marker").exists()
                        }
                        
                        if version_info["has_completion_marker"]:
                            try:
                                with open(item / ".complete_marker", 'r') as f:
                                    marker_data = json.load(f)
                                    version_info["completion_data"] = marker_data
                            except:
                                pass
                        
                        versions.append(version_info)
                        
            else:
                # For GCS, list all directories and check for completion markers
                base_path = STORAGE_CONFIG["gcs"]["base_path"]
                prefix = f"{base_path}/{video_id}/"
                files = self.gcs_service.list_files(prefix)
                
                dir_info = {}
                for file_path in files:
                    if "/" in file_path[len(prefix):]:
                        dir_name = file_path[len(prefix):].split("/")[0]
                        if dir_name not in dir_info:
                            dir_info[dir_name] = {"files": [], "has_marker": False}
                        
                        dir_info[dir_name]["files"].append(file_path)
                        
                        if file_path.endswith("/.complete_marker"):
                            dir_info[dir_name]["has_marker"] = True
                
                for dir_name, info in dir_info.items():
                    # Determine if directory is complete based on presence of completion marker
                    is_complete = info["has_marker"]
                    status = "complete" if is_complete else "processing"
                    
                    version_info = {
                        "directory": f"{prefix}{dir_name}",
                        "timestamp": dir_name.split('_')[0] + "_" + dir_name.split('_')[1] if '_' in dir_name else dir_name,
                        "status": status,
                        "has_completion_marker": info["has_marker"],
                        "file_count": len(info["files"])
                    }
                    versions.append(version_info)
            
            # Sort by timestamp (newest first)
            versions.sort(key=lambda x: x["timestamp"], reverse=True)
            
            self.logger.info(f"Found {len(versions)} versions for video {video_id}")
            return versions
            
        except Exception as e:
            self.logger.error(f"Error listing report versions: {e}")
            return []
    
    def cleanup_old_versions(self, video_id: str, keep_count: int = 5) -> bool:
        """
        Clean up old report versions, keeping only the most recent ones.
        
        Args:
            video_id: Video identifier
            keep_count: Number of versions to keep
            
        Returns:
            bool: True if cleanup was successful
        """
        try:
            versions = self.list_report_versions(video_id)
            complete_versions = [v for v in versions if v["status"] == "complete"]
            
            if len(complete_versions) <= keep_count:
                self.logger.info(f"No cleanup needed for {video_id}: {len(complete_versions)} versions (keeping {keep_count})")
                return True
            
            versions_to_delete = complete_versions[keep_count:]
            
            for version in versions_to_delete:
                if self.storage_backend == StorageBackend.LOCAL:
                    dir_path = Path(version["directory"])
                    if dir_path.exists():
                        shutil.rmtree(dir_path)
                        self.logger.info(f"Deleted old local version: {dir_path}")
                else:
                    # For GCS, delete all files in the directory
                    base_path = STORAGE_CONFIG["gcs"]["base_path"]
                    prefix = version["directory"].replace(f"{base_path}/", "") + "/"
                    files = self.gcs_service.list_files(prefix)
                    
                    for file_path in files:
                        # Delete each file (GCS doesn't have directories)
                        try:
                            from google.cloud import storage
                            client = storage.Client()
                            bucket = client.bucket(STORAGE_CONFIG["gcs"]["bucket_name"])
                            blob = bucket.blob(file_path)
                            blob.delete()
                        except Exception as e:
                            self.logger.warning(f"Failed to delete GCS file {file_path}: {e}")
                    
                    self.logger.info(f"Deleted old GCS version: {version['directory']}")
            
            self.logger.info(f"Cleaned up {len(versions_to_delete)} old versions for video {video_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error cleaning up old versions: {e}")
            return False
    
    def _list_files_in_directory(self, directory: str) -> List[str]:
        """List all files in a directory."""
        try:
            if self.storage_backend == StorageBackend.LOCAL:
                dir_path = Path(directory)
                if dir_path.exists():
                    return [f.name for f in dir_path.iterdir() if f.is_file()]
                return []
            else:
                # For GCS, list files with the directory prefix
                files = self.gcs_service.list_files(directory + "/")
                return [f.split("/")[-1] for f in files if not f.endswith("/")]
        except Exception as e:
            self.logger.error(f"Error listing files in directory: {e}")
            return []

# Global instance
timestamped_storage = TimestampedStorageService() 
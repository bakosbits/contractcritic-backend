import os
import uuid
import requests
from typing import Optional, Dict, Any
import mimetypes

class VercelBlobService:
    def __init__(self):
        self.token = os.getenv("BLOB_READ_WRITE_TOKEN")
        if not self.token:
            raise ValueError("BLOB_READ_WRITE_TOKEN must be set in environment variables")
        self.base_url = "https://blob.vercel-storage.com"
    
    def upload_file(self, file_content: bytes, filename: str, content_type: str = None) -> Optional[Dict[str, Any]]:
        """
        Upload file to Vercel Blob Storage and return file info
        
        Args:
            file_content: The file content as bytes
            filename: Original filename
            content_type: MIME type of the file
            
        Returns:
            Dict with url, pathname, contentType, contentDisposition if successful, None otherwise
        """
        try:
            # Generate unique filename to avoid conflicts
            file_extension = os.path.splitext(filename)[1]
            unique_filename = f"{uuid.uuid4()}{file_extension}"
            
            # Guess content type if not provided
            if not content_type:
                content_type, _ = mimetypes.guess_type(filename)
                if not content_type:
                    content_type = 'application/octet-stream'
            
            # Prepare headers
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": content_type,
                "x-content-type": content_type,
                "x-add-random-suffix": "1"  # Let Vercel add random suffix for uniqueness
            }
            
            # Upload to Vercel Blob Storage
            upload_url = f"{self.base_url}/{filename}"  # Use original filename, Vercel will make it unique
            
            response = requests.put(
                upload_url,
                data=file_content,
                headers=headers
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'url': result.get('url'),
                    'pathname': result.get('pathname'),
                    'content_type': result.get('contentType', content_type),
                    'content_disposition': result.get('contentDisposition'),
                    'size': len(file_content)
                }
            else:
                print(f"Upload failed with status {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            print(f"Error uploading file to Vercel Blob: {e}")
            return None
    
    def delete_file(self, file_url: str) -> bool:
        """
        Delete file from Vercel Blob Storage
        
        Args:
            file_url: The URL of the file to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.token}"
            }
            
            # For deletion, we need to use the DELETE method on the file URL
            response = requests.delete(file_url, headers=headers)
            
            return response.status_code in [200, 204, 404]  # 404 means already deleted
            
        except Exception as e:
            print(f"Error deleting file from Vercel Blob: {e}")
            return False
    
    def get_file_info(self, file_url: str) -> Optional[Dict[str, Any]]:
        """
        Get file information from Vercel Blob Storage
        
        Args:
            file_url: The URL of the file
            
        Returns:
            Dict with file info if successful, None otherwise
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.token}"
            }
            
            response = requests.head(file_url, headers=headers)
            
            if response.status_code == 200:
                return {
                    'url': file_url,
                    'content_type': response.headers.get('content-type'),
                    'content_length': response.headers.get('content-length'),
                    'last_modified': response.headers.get('last-modified'),
                    'etag': response.headers.get('etag')
                }
            
            return None
            
        except Exception as e:
            print(f"Error getting file info from Vercel Blob: {e}")
            return None
    
    def generate_signed_url(self, file_url: str, expires_in: int = 3600) -> Optional[str]:
        """
        Generate a signed URL for temporary access (if supported by Vercel Blob)
        
        Args:
            file_url: The URL of the file
            expires_in: Expiration time in seconds
            
        Returns:
            Signed URL if successful, original URL otherwise
        """
        # Vercel Blob Storage URLs are typically public by default
        # This method is here for future compatibility if signed URLs are needed
        return file_url
    
    def list_files(self, prefix: str = "") -> Optional[list]:
        """
        List files in Vercel Blob Storage (if supported)
        
        Args:
            prefix: Prefix to filter files
            
        Returns:
            List of file info dicts if successful, None otherwise
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.token}"
            }
            
            # This endpoint might not be available in all Vercel Blob plans
            list_url = f"{self.base_url}/"
            if prefix:
                list_url += f"?prefix={prefix}"
            
            response = requests.get(list_url, headers=headers)
            
            if response.status_code == 200:
                return response.json().get('blobs', [])
            
            return None
            
        except Exception as e:
            print(f"Error listing files from Vercel Blob: {e}")
            return None

# Global instance
blob_service = VercelBlobService()

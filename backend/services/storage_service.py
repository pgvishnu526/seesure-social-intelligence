"""
Storage service for SocialPulse - handles both S3 and local storage
"""

import os
import json
import shutil
from typing import Optional, Dict, Any, List
from pathlib import Path
from datetime import datetime
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
import logging

logger = logging.getLogger(__name__)


class StorageService:
    """Unified storage service supporting S3 and local fallback"""
    
    def __init__(self):
        self.use_s3 = False
        self.s3_client = None
        self.bucket_name = os.getenv("S3_BUCKET_NAME", "socialpulse-bucket")
        self.local_data_dir = Path("data")
        
        # Initialize S3 if credentials are available
        self._init_s3()
        
        # Ensure local directory exists
        self.local_data_dir.mkdir(exist_ok=True)
    
    def _init_s3(self):
        """Initialize S3 client if credentials are available"""
        try:
            aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
            aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
            aws_region = os.getenv("AWS_REGION", "us-east-1")
            
            if aws_access_key and aws_secret_key:
                self.s3_client = boto3.client(
                    's3',
                    aws_access_key_id=aws_access_key,
                    aws_secret_access_key=aws_secret_key,
                    region_name=aws_region
                )
                
                # Test S3 connection
                self.s3_client.head_bucket(Bucket=self.bucket_name)
                self.use_s3 = True
                logger.info(f"S3 storage initialized: {self.bucket_name}")
                
            else:
                logger.info("AWS credentials not found, using local storage")
                
        except (ClientError, NoCredentialsError) as e:
            logger.warning(f"S3 initialization failed: {e}. Using local storage.")
        except Exception as e:
            logger.error(f"Unexpected S3 error: {e}. Using local storage.")
    
    def _get_storage_path(self, analysis_id: str, file_type: str, filename: str = "") -> str:
        """Generate storage path for a file"""
        now = datetime.utcnow()
        year = now.strftime("%Y")
        month = now.strftime("%m")
        day = now.strftime("%d")
        
        if file_type == "raw":
            path = f"raw/{year}/{month}/{day}/{analysis_id}/{filename or 'input.png'}"
        elif file_type == "processed":
            path = f"processed/{year}/{month}/{day}/{analysis_id}/{filename}"
        elif file_type == "research":
            path = f"research/{year}/{month}/{day}/{analysis_id}/{filename}"
        elif file_type == "analysis":
            path = f"analysis/{year}/{month}/{day}/{analysis_id}/{filename}"
        elif file_type == "reports":
            path = f"reports/{year}/{month}/{day}/{analysis_id}/{filename}"
        else:
            path = f"misc/{year}/{month}/{day}/{analysis_id}/{filename}"
        
        return path
    
    async def store_image(self, analysis_id: str, image_data: bytes, filename: str = "input.png") -> str:
        """Store uploaded image"""
        storage_path = self._get_storage_path(analysis_id, "raw", filename)
        
        try:
            if self.use_s3:
                # Store in S3
                self.s3_client.put_object(
                    Bucket=self.bucket_name,
                    Key=storage_path,
                    Body=image_data,
                    ContentType="image/png"
                )
                url = f"s3://{self.bucket_name}/{storage_path}"
                logger.info(f"Image stored in S3: {storage_path}")
            else:
                # Store locally
                local_path = self.local_data_dir / storage_path
                local_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(local_path, 'wb') as f:
                    f.write(image_data)
                
                url = str(local_path)
                logger.info(f"Image stored locally: {local_path}")
            
            return url
            
        except Exception as e:
            logger.error(f"Failed to store image for {analysis_id}: {e}")
            raise
    
    async def store_json(self, analysis_id: str, data: Dict[Any, Any], 
                        file_type: str, filename: str) -> str:
        """Store JSON data"""
        storage_path = self._get_storage_path(analysis_id, file_type, filename)
        json_data = json.dumps(data, indent=2, default=str)
        
        try:
            if self.use_s3:
                # Store in S3
                self.s3_client.put_object(
                    Bucket=self.bucket_name,
                    Key=storage_path,
                    Body=json_data.encode('utf-8'),
                    ContentType="application/json"
                )
                url = f"s3://{self.bucket_name}/{storage_path}"
            else:
                # Store locally
                local_path = self.local_data_dir / storage_path
                local_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(local_path, 'w', encoding='utf-8') as f:
                    f.write(json_data)
                
                url = str(local_path)
            
            logger.debug(f"JSON stored: {storage_path}")
            return url
            
        except Exception as e:
            logger.error(f"Failed to store JSON for {analysis_id}: {e}")
            raise
    
    async def load_json(self, analysis_id: str, file_type: str, filename: str) -> Optional[Dict[Any, Any]]:
        """Load JSON data"""
        storage_path = self._get_storage_path(analysis_id, file_type, filename)
        
        try:
            if self.use_s3:
                # Load from S3
                response = self.s3_client.get_object(
                    Bucket=self.bucket_name,
                    Key=storage_path
                )
                json_data = response['Body'].read().decode('utf-8')
            else:
                # Load locally
                local_path = self.local_data_dir / storage_path
                if not local_path.exists():
                    return None
                
                with open(local_path, 'r', encoding='utf-8') as f:
                    json_data = f.read()
            
            return json.loads(json_data)
            
        except (ClientError, FileNotFoundError):
            logger.warning(f"JSON file not found: {storage_path}")
            return None
        except Exception as e:
            logger.error(f"Failed to load JSON from {storage_path}: {e}")
            return None
    
    async def get_image_url(self, analysis_id: str, filename: str = "input.png") -> Optional[str]:
        """Get URL for accessing stored image"""
        storage_path = self._get_storage_path(analysis_id, "raw", filename)
        
        try:
            if self.use_s3:
                # Generate presigned URL for S3
                url = self.s3_client.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': self.bucket_name, 'Key': storage_path},
                    ExpiresIn=3600  # 1 hour
                )
                return url
            else:
                # Return local file path
                local_path = self.local_data_dir / storage_path
                if local_path.exists():
                    # In a production setup, this would be served by a web server
                    # For development, we'll return the relative path
                    return f"/data/{storage_path}"
                else:
                    return None
                    
        except Exception as e:
            logger.error(f"Failed to get image URL for {analysis_id}: {e}")
            return None
    
    async def store_analysis_state(self, analysis_id: str, state_data: Dict[Any, Any]) -> str:
        """Store complete analysis state"""
        return await self.store_json(analysis_id, state_data, "analysis", "state.json")
    
    async def load_analysis_state(self, analysis_id: str) -> Optional[Dict[Any, Any]]:
        """Load complete analysis state"""
        return await self.load_json(analysis_id, "analysis", "state.json")
    
    async def store_final_report(self, analysis_id: str, report_data: Dict[Any, Any]) -> str:
        """Store final analysis report"""
        return await self.store_json(analysis_id, report_data, "reports", "report.json")
    
    async def load_final_report(self, analysis_id: str) -> Optional[Dict[Any, Any]]:
        """Load final analysis report"""
        return await self.load_json(analysis_id, "reports", "report.json")
    
    async def list_analyses(self, limit: int = 100) -> List[Dict[str, Any]]:
        """List recent analyses"""
        analyses = []
        
        try:
            if self.use_s3:
                # List S3 objects
                response = self.s3_client.list_objects_v2(
                    Bucket=self.bucket_name,
                    Prefix="reports/",
                    MaxKeys=limit
                )
                
                for obj in response.get('Contents', []):
                    if obj['Key'].endswith('report.json'):
                        # Extract analysis ID from path
                        parts = obj['Key'].split('/')
                        if len(parts) >= 5:
                            analysis_id = parts[4]
                            analyses.append({
                                'analysis_id': analysis_id,
                                'timestamp': obj['LastModified'].isoformat(),
                                'size': obj['Size']
                            })
            else:
                # List local files
                reports_dir = self.local_data_dir / "reports"
                if reports_dir.exists():
                    for report_file in reports_dir.rglob("report.json"):
                        # Extract analysis ID from path
                        parts = report_file.parts
                        if len(parts) >= 6:  # data/reports/year/month/day/analysis_id/report.json
                            analysis_id = parts[-2]
                            stat = report_file.stat()
                            analyses.append({
                                'analysis_id': analysis_id,
                                'timestamp': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                                'size': stat.st_size
                            })
            
            # Sort by timestamp (newest first)
            analyses.sort(key=lambda x: x['timestamp'], reverse=True)
            return analyses[:limit]
            
        except Exception as e:
            logger.error(f"Failed to list analyses: {e}")
            return []
    
    async def cleanup_old_data(self, days_old: int = 30):
        """Clean up data older than specified days"""
        cutoff_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        cutoff_date = cutoff_date.replace(day=cutoff_date.day - days_old)
        
        logger.info(f"Cleaning up data older than {cutoff_date}")
        
        try:
            if self.use_s3:
                # S3 lifecycle policies are recommended for this
                logger.info("S3 cleanup should be handled by lifecycle policies")
            else:
                # Clean up local files
                for date_dir in self.local_data_dir.iterdir():
                    if date_dir.is_dir():
                        try:
                            # Parse directory date (assuming YYYY/MM/DD structure)
                            year_dir = date_dir
                            if year_dir.name.isdigit():
                                for month_dir in year_dir.iterdir():
                                    if month_dir.is_dir() and month_dir.name.isdigit():
                                        for day_dir in month_dir.iterdir():
                                            if day_dir.is_dir() and day_dir.name.isdigit():
                                                dir_date = datetime(
                                                    int(year_dir.name),
                                                    int(month_dir.name),
                                                    int(day_dir.name)
                                                )
                                                if dir_date < cutoff_date:
                                                    shutil.rmtree(day_dir)
                                                    logger.info(f"Removed old data: {day_dir}")
                        except (ValueError, OSError) as e:
                            logger.warning(f"Error cleaning directory {date_dir}: {e}")
            
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")


# Global storage service instance
storage_service = StorageService()
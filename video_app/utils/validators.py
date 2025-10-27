"""
Video validation utilities.

This module contains all validation functions for video files,
including file format validation, size checks, and comprehensive validation.
"""
import os
import json
import uuid
import logging
import tempfile
import subprocess
from django.core.exceptions import ValidationError

logger = logging.getLogger(__name__)


def validate_video_size(file):
    """Ensures that the uploaded video file is no larger than 100 MB."""
    max_size = 100.5 * 1024 * 1024  
    if file.size > max_size:
        raise ValidationError(f'File is too large. Maximum: 100MB, Current: {file.size / 1024 / 1024:.2f}MB')


def comprehensive_video_validator(file):
    """
    Comprehensive video file validator that performs all critical checks
    before any processing begins. This should be used in Django form validation.
    """
    try:
        if not file:
            raise ValidationError("No file uploaded.")
        
        if file.size == 0:
            raise ValidationError("The uploaded file is empty.")
        
        max_size = 100.5 * 1024 * 1024
        if file.size > max_size:
            raise ValidationError(f'File is too large. Maximum: 100MB, Current: {file.size / 1024 / 1024:.2f}MB')
        
        allowed_extensions = ['mp4', 'avi', 'mov', 'mkv']
        file_extension = os.path.splitext(file.name)[1].lower().lstrip('.')
        
        if file_extension not in allowed_extensions:
            raise ValidationError(f'Unsupported file format: .{file_extension}. '
                                f'Allowed formats: {", ".join(allowed_extensions)}')
        
        allowed_content_types = [
            'video/mp4', 'video/quicktime', 'video/x-msvideo', 
            'video/x-matroska', 'application/octet-stream'
        ]
        
        if hasattr(file, 'content_type') and file.content_type:
            if file.content_type not in allowed_content_types:
                logger.warning(f"Suspicious content type: {file.content_type} for file: {file.name}")
        
        try:
            result = subprocess.run(['ffmpeg', '-version'], 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=5)
            if result.returncode != 0:
                raise ValidationError("Video processing system is not available. Please try again later.")
        except subprocess.TimeoutExpired:
            raise ValidationError("Video processing system is not responding. Please try again later.")
        except FileNotFoundError:
            raise ValidationError("Video processing system is not installed. Contact administrator.")
        
        # Deep file validation using temporary file
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file_extension}') as temp_file:
                # Write file content to temporary file for validation
                for chunk in file.chunks():
                    temp_file.write(chunk)
                temp_file.flush()
                temp_path = temp_file.name
            
            try:
                # Validate using ffprobe
                cmd = [
                    'ffprobe', '-v', 'quiet', '-print_format', 'json', 
                    '-show_format', '-show_streams', temp_path
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                
                if result.returncode != 0:
                    raise ValidationError("The file is corrupted or has an unsupported video format.")
                
                # Parse and validate probe data
                try:
                    probe_data = json.loads(result.stdout)
                    
                    # Check for video streams
                    video_streams = [stream for stream in probe_data.get('streams', []) 
                                   if stream.get('codec_type') == 'video']
                    
                    if not video_streams:
                        raise ValidationError("No video streams found in file.")
                    
                    # Check duration
                    format_info = probe_data.get('format', {})
                    duration = float(format_info.get('duration', 0))
                    
                    if duration <= 0:
                        raise ValidationError("Video has no valid duration.")
                    
                    if duration > 7200:  # 2 hours max
                        raise ValidationError(f'Video is too long. Maximum: 2 hours, '
                                            f'Current: {duration/3600:.1f} hours')
                    
                    if duration < 1:  # Minimum 1 second
                        raise ValidationError("Video is too short (Minimum: 1 second).")
                    
                    # Check video properties
                    video_stream = video_streams[0]
                    width = video_stream.get('width', 0)
                    height = video_stream.get('height', 0)
                    
                    if width <= 0 or height <= 0:
                        raise ValidationError("Video has invalid dimensions.")
                    
                    if width > 3840 or height > 2160:  # 4K max
                        raise ValidationError(f'Video resolution is too high. Maximum: 4K (3840x2160), '
                                            f'Current: {width}x{height}')
                    
                    if width < 320 or height < 240:  # Minimum resolution
                        raise ValidationError(f'Video resolution is too low. Minimum: 320x240, '
                                            f'Current: {width}x{height}')
                    
                    logger.info(f"Video validation successful: {file.name} "
                              f"({file.size / 1024 / 1024:.2f}MB, {duration:.1f}s, {width}x{height})")
                    
                except json.JSONDecodeError:
                    raise ValidationError("Could not analyze video file information.")
                    
            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_path)
                except OSError:
                    pass
                    
        except subprocess.TimeoutExpired:
            raise ValidationError("Video validation failed (timeout). "
                                "The file may be too complex or corrupted.")
        
        # Reset file pointer after reading
        if hasattr(file, 'seek'):
            file.seek(0)
            
        return file
        
    except ValidationError:
        # Reset file pointer before re-raising
        if hasattr(file, 'seek'):
            file.seek(0)
        raise
    except Exception as e:
        # Reset file pointer before raising new error
        if hasattr(file, 'seek'):
            file.seek(0)
        logger.error(f"Unexpected error during comprehensive video validation: {str(e)}")
        raise ValidationError(f"Unexpected error during video validation: {str(e)}")


def quick_video_format_check(file_path):
    """
    Quick video format check using file extension and magic bytes.
    Used for rapid validation without deep analysis.
    """
    try:
        if not os.path.exists(file_path):
            return False, "File does not exist"
        
        if os.path.getsize(file_path) == 0:
            return False, "File is empty"
        
        # Check file extension
        allowed_extensions = ['.mp4', '.avi', '.mov', '.mkv']
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext not in allowed_extensions:
            return False, f"Unsupported extension: {file_ext}"
        
        # Check magic bytes for common video formats
        try:
            with open(file_path, 'rb') as f:
                header = f.read(12)
                
                # MP4 magic bytes
                if len(header) >= 8 and header[4:8] == b'ftyp':
                    return True, "Valid MP4 format"
                
                # AVI magic bytes
                if len(header) >= 12 and header[0:4] == b'RIFF' and header[8:12] == b'AVI ':
                    return True, "Valid AVI format"
                
                # MOV/QuickTime magic bytes (similar to MP4)
                if len(header) >= 8 and header[4:8] in [b'ftyp', b'mdat', b'moov']:
                    return True, "Valid MOV format"
                
                # For other formats, trust the extension
                return True, f"Format appears valid based on extension: {file_ext}"
                
        except IOError as e:
            return False, f"Cannot read file: {str(e)}"
        
    except Exception as e:
        return False, f"Error checking format: {str(e)}"


def build_ffprobe_command(video_path: str):
    """Build FFprobe command for video analysis."""
    return [
        'ffprobe', '-v', 'quiet', '-print_format', 'json',
        '-show_format', '-show_streams', video_path
    ]


def extract_video_stream(video_metadata):
    """Extract video stream from metadata."""
    for stream in video_metadata.get('streams', []):
        if stream.get('codec_type') == 'video':
            return stream
    return None


def extract_format_info(video_metadata):
    """Extract format information from video metadata."""
    format_data = video_metadata.get('format', {})
    return {
        'duration': float(format_data.get('duration', 0)),
        'size': int(format_data.get('size', 0)),
        'format': format_data.get('format_name', 'unknown'),
    }


def extract_stream_info(video_stream):
    """Extract stream information from video stream."""
    if not video_stream:
        return {}
    return {
        'width': video_stream.get('width', 0),
        'height': video_stream.get('height', 0),
        'codec': video_stream.get('codec_name', 'unknown'),
    }


def build_video_info(video_metadata, video_stream):
    """Build video information dictionary."""
    video_info = extract_format_info(video_metadata)
    video_info.update(extract_stream_info(video_stream))
    return video_info


def execute_ffprobe_command(video_path):
    """Execute ffprobe command and return result."""
    command = build_ffprobe_command(video_path)
    return subprocess.run(command, capture_output=True, text=True)


def process_ffprobe_result(result):
    """Process ffprobe result and return video info."""
    if result.returncode == 0:
        metadata = json.loads(result.stdout)
        video_stream = extract_video_stream(metadata)
        return build_video_info(metadata, video_stream)
    else:
        logger.error(f"FFprobe error: {result.stderr}")
        return {}


def get_video_file_info(video_path: str):
    """Get basic information about video file using ffprobe."""
    try:
        result = execute_ffprobe_command(video_path)
        return process_ffprobe_result(result)
    except Exception as e:
        logger.error(f"Error getting video info: {str(e)}")
        return {}


def validate_video_for_processing(video_instance):
    """
    Comprehensive validation before queuing video for processing.
    Checks file existence, accessibility, FFmpeg availability, and basic video properties.
    """
    try:
        if not video_instance or not video_instance.video_file:
            logger.error("No video instance or video file provided")
            return False
        
        try:
            video_path = video_instance.video_file.path
            
            if not os.path.exists(video_path):
                logger.error(f"Video file does not exist: {video_path}")
                return False
            
            if not os.access(video_path, os.R_OK):
                logger.error(f"Video file is not readable: {video_path}")
                return False
            
            file_size = os.path.getsize(video_path)
            if file_size == 0:
                logger.error(f"Video file is empty: {video_path}")
                return False
            
            max_size = 100.5 * 1024 * 1024  # 100.5 MB
            if file_size > max_size:
                logger.error(f"Video file too large: {file_size / 1024 / 1024:.2f}MB")
                return False
                
        except (AttributeError, OSError) as e:
            logger.error(f"Error accessing video file for {video_instance.title}: {str(e)}")
            return False
        
        try:
            result = subprocess.run(['ffmpeg', '-version'], 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=10)
            if result.returncode != 0:
                logger.error("FFmpeg is not available or not working properly")
                return False
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            logger.error(f"FFmpeg availability check failed: {str(e)}")
            return False
        
        try:
            result = subprocess.run([
                'ffprobe', '-v', 'quiet', '-print_format', 'json', 
                '-show_format', video_path
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                logger.error(f"Video file format validation failed for: {video_path}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error(f"Video format check timeout for: {video_path}")
            return False
        except Exception as e:
            logger.error(f"Video format check error: {str(e)}")
            return False
        
        if not video_instance.title or not video_instance.title.strip():
            logger.error("Video title is missing or empty")
            return False
        
        if not video_instance.category:
            logger.error("Video category is missing")
            return False
        
        logger.info(f"Video validation successful for: {video_instance.title} ({file_size / 1024 / 1024:.2f}MB)")
        return True
        
    except Exception as e:
        logger.error(f"Unexpected error during video validation: {str(e)}")
        return False
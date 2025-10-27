"""
Thumbnail generation utilities.

This module handles thumbnail creation and processing for video files.
"""
import os
import subprocess
import logging
from typing import List

logger = logging.getLogger(__name__)


def build_thumbnail_command(video_path: str, output_path: str, timestamp: str) -> List[str]:
    """Build FFmpeg command for thumbnail generation."""
    return [
        'ffmpeg', 
        '-i', video_path, 
        '-ss', timestamp, 
        '-vframes', '1',
        '-vf', 'scale=320:180:force_original_aspect_ratio=decrease,pad=320:180:(ow-iw)/2:(oh-ih)/2',
        '-q:v', '2',  
        '-f', 'image2',
        output_path, 
        '-y'
    ]


def execute_thumbnail_generation(command: List[str], output_path: str) -> bool:
    """Execute thumbnail generation command."""
    try:
        result = subprocess.run(
            command, 
            capture_output=True, 
            text=True, 
            timeout=30  
        )

        if result.returncode == 0 and os.path.exists(output_path):
            if os.path.getsize(output_path) > 0:
                logger.info(f"Generated thumbnail: {output_path}")
                return True
            else:
                logger.error(f"Generated thumbnail is empty: {output_path}")
                return False
        else:
            logger.error(f"Failed to generate thumbnail. Return code: {result.returncode}")
            if result.stderr:
                logger.error(f"FFmpeg stderr: {result.stderr}")
            if result.stdout:
                logger.info(f"FFmpeg stdout: {result.stdout}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error(f"Thumbnail generation timed out for: {output_path}")
        return False
    except Exception as e:
        logger.error(f"Exception during thumbnail generation: {str(e)}")
        return False


def generate_video_thumbnail(video_path: str, output_path: str, timestamp: str = "00:00:10") -> bool:
    """Generate thumbnail image from video at specified timestamp."""
    try:
        command = build_thumbnail_command(video_path, output_path, timestamp)
        return execute_thumbnail_generation(command, output_path)
    except Exception as e:
        logger.error(f"Error generating thumbnail: {str(e)}")
        return False


def generate_video_thumbnail_for_instance(video_instance):
    """
    Generate and save thumbnail for a video instance.
    Automatically creates thumbnail at 10-second mark and saves to instance.
    """
    import os
    from django.conf import settings
    from django.core.files.base import ContentFile
    
    try:
        if not video_instance.video_file:
            logger.error(f"No video file found for video ID {video_instance.id}")
            return False
            
        video_path = video_instance.video_file.path
        
        if not os.path.exists(video_path):
            logger.error(f"Video file does not exist: {video_path} for video ID {video_instance.id}")
            return False
            
        if not os.access(video_path, os.R_OK):
            logger.error(f"Video file not readable: {video_path} for video ID {video_instance.id}")
            return False
        
        video_name = os.path.splitext(os.path.basename(video_path))[0]
        thumbnail_filename = f"{video_name}_thumbnail.jpg"
        
        temp_thumbnail_path = os.path.join(settings.MEDIA_ROOT, 'temp', thumbnail_filename)
        os.makedirs(os.path.dirname(temp_thumbnail_path), exist_ok=True)
        
        timestamps = ["00:00:10", "00:00:05", "00:00:02", "00:00:01"]
        success = False
        
        for timestamp in timestamps:
            logger.info(f"Attempting thumbnail generation at {timestamp} for video ID {video_instance.id}")
            success = generate_video_thumbnail(video_path, temp_thumbnail_path, timestamp)
            if success and os.path.exists(temp_thumbnail_path):
                if os.path.getsize(temp_thumbnail_path) > 0:
                    logger.info(f"Successfully generated thumbnail at {timestamp} for video ID {video_instance.id}")
                    break
                else:
                    logger.warning(f"Empty thumbnail file generated at {timestamp} for video ID {video_instance.id}")
                    success = False
            else:
                logger.warning(f"Failed to generate thumbnail at {timestamp} for video ID {video_instance.id}")
        
        if success and os.path.exists(temp_thumbnail_path) and os.path.getsize(temp_thumbnail_path) > 0:
            try:
                with open(temp_thumbnail_path, 'rb') as f:
                    thumbnail_content = f.read()
                
                if len(thumbnail_content) == 0:
                    logger.error(f"Thumbnail file is empty for video ID {video_instance.id}")
                    return False
                
                video_instance.thumbnail.save(
                    thumbnail_filename,
                    ContentFile(thumbnail_content),
                    save=True
                )
                
                logger.info(f"Thumbnail saved successfully for video ID {video_instance.id}")
                
            except Exception as save_error:
                logger.error(f"Failed to save thumbnail to database for video ID {video_instance.id}: {str(save_error)}")
                return False
            finally:
                try:
                    if os.path.exists(temp_thumbnail_path):
                        os.remove(temp_thumbnail_path)
                except Exception as cleanup_error:
                    logger.warning(f"Failed to cleanup temp thumbnail for video ID {video_instance.id}: {str(cleanup_error)}")
                
            return True
        else:
            logger.error(f"Failed to generate thumbnail file for video ID {video_instance.id} after trying all timestamps")
            return False
            
    except Exception as e:
        logger.error(f"Error generating thumbnail for video ID {video_instance.id}: {str(e)}")
        return False


def create_default_thumbnail(video_instance):
    """
    Create a default thumbnail for videos where automatic generation fails.
    This creates a simple colored placeholder image with the video title.
    """
    try:
        try:
            from PIL import Image, ImageDraw, ImageFont
        except ImportError:
            logger.error("Pillow not available for default thumbnail generation")
            return False
            
        from django.core.files.base import ContentFile
        import io
        
        img = Image.new('RGB', (320, 180), color=(45, 45, 45))
        draw = ImageDraw.Draw(img)
        
        try:
            font = ImageFont.truetype("arial.ttf", 24)
            small_font = ImageFont.truetype("arial.ttf", 16)
        except:
            try:
                font = ImageFont.load_default()
                small_font = ImageFont.load_default()
            except:
                font = None
                small_font = None
        
        title_text = video_instance.title[:30] + "..." if len(video_instance.title) > 30 else video_instance.title
        
        if font:
            bbox = draw.textbbox((0, 0), title_text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            x = (320 - text_width) // 2
            y = (180 - text_height) // 2 - 10
            
            draw.text((x + 2, y + 2), title_text, fill=(0, 0, 0), font=font)  
            draw.text((x, y), title_text, fill=(255, 255, 255), font=font)    
            
            if small_font:
                label_bbox = draw.textbbox((0, 0), "VIDEO", font=small_font)
                label_width = label_bbox[2] - label_bbox[0]
                label_x = (320 - label_width) // 2
                draw.text((label_x, y + text_height + 10), "VIDEO", fill=(150, 150, 150), font=small_font)
        
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='JPEG', quality=85)
        img_buffer.seek(0)
        
        filename = f"default_thumbnail_{video_instance.id}.jpg"
        
        video_instance.thumbnail.save(
            filename,
            ContentFile(img_buffer.read()),
            save=True
        )
        
        logger.info(f"Default thumbnail created for video ID {video_instance.id}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create default thumbnail for video ID {video_instance.id}: {str(e)}")
        return False


def regenerate_thumbnail_job(video_id):
    """
    Job function for asynchronous thumbnail regeneration.
    This function is called by django-rq for background processing.
    """
    try:
        from ..models import Video
        
        video = Video.objects.get(id=video_id)
        
        if video.thumbnail:
            video.thumbnail.delete(save=False)
        
        success = generate_video_thumbnail_for_instance(video)
        
        if success:
            logger.info(f"Thumbnail regeneration successful for video ID {video_id}")
        else:
            logger.error(f"Thumbnail regeneration failed for video ID {video_id}")
            success = create_default_thumbnail(video)
        
        return success
        
    except Exception as e:
        logger.error(f"Error in thumbnail regeneration job for video ID {video_id}: {str(e)}")
        return False

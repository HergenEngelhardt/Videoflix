"""
Utility functions for video processing and HLS conversion.
"""
import os
import subprocess
from django.conf import settings
import django_rq


def convert_video_to_hls(video_instance):
    """
    Convert video to HLS format with multiple resolutions.
    This runs in background using Django RQ.
    """
    if not video_instance.video_file:
        return False
    
    video_path = video_instance.video_file.path
    video_id = video_instance.id
    
    # Create HLS directory
    hls_dir = os.path.join(settings.MEDIA_ROOT, 'hls', str(video_id))
    os.makedirs(hls_dir, exist_ok=True)
    
    # Define resolutions
    resolutions = [
        {'name': '480p', 'width': 854, 'height': 480, 'bitrate': '1000k'},
        {'name': '720p', 'width': 1280, 'height': 720, 'bitrate': '2500k'},
        {'name': '1080p', 'width': 1920, 'height': 1080, 'bitrate': '5000k'},
    ]
    
    try:
        for resolution in resolutions:
            res_dir = os.path.join(hls_dir, resolution['name'])
            os.makedirs(res_dir, exist_ok=True)
            
            output_path = os.path.join(res_dir, 'index.m3u8')
            
            # FFmpeg command for HLS conversion
            cmd = [
                'ffmpeg',
                '-i', video_path,
                '-c:v', 'libx264',
                '-c:a', 'aac',
                '-strict', 'experimental',
                '-ac', '2',
                '-b:a', '128k',
                '-ar', '44100',
                '-vf', f'scale={resolution["width"]}:{resolution["height"]}',
                '-b:v', resolution['bitrate'],
                '-maxrate', resolution['bitrate'],
                '-bufsize', str(int(resolution['bitrate'][:-1]) * 2) + 'k',
                '-hls_time', '10',
                '-hls_list_size', '0',
                '-hls_segment_filename', os.path.join(res_dir, '%03d.ts'),
                '-f', 'hls',
                output_path,
                '-y'  # Overwrite output file
            ]
            
            # Run FFmpeg
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"Error converting {resolution['name']}: {result.stderr}")
                continue
        
        # Update video instance
        video_instance.hls_processed = True
        video_instance.hls_path = f'hls/{video_id}/'
        video_instance.save()
        
        return True
        
    except Exception as e:
        print(f"Error in HLS conversion: {str(e)}")
        return False


def queue_video_conversion(video_instance):
    """
    Queue video for HLS conversion in background.
    """
    queue = django_rq.get_queue('default')
    queue.enqueue(convert_video_to_hls, video_instance)


def cleanup_hls_files(video_instance):
    """
    Clean up HLS files when video is deleted.
    """
    if video_instance.hls_path:
        hls_dir = os.path.join(settings.MEDIA_ROOT, video_instance.hls_path)
        if os.path.exists(hls_dir):
            import shutil
            shutil.rmtree(hls_dir)
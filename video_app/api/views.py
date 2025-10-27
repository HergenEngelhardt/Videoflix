from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.http import HttpResponse, Http404
from django.conf import settings
from django.shortcuts import get_object_or_404
import os

from .serializers import VideoListSerializer
from ..models import Video


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def video_list_view(request):
    """
    GET /api/video/
    Get list of all available videos grouped by categories and ordered by creation date DESC.
    """
    videos = Video.objects.select_related('category').order_by('-created_at')
    serializer = VideoListSerializer(videos, many=True, context={'request': request})

    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_view(request):
    """
    GET /api/video/dashboard/
    Get dashboard with hero video and videos grouped by categories.
    Returns:
    - hero_video: Featured/latest video for hero section
    - categories: Dict with category names as keys and video lists as values
    """
    from ..utils.core import get_dashboard_empty_response, build_categories_dict, serialize_categories
    
    videos = Video.objects.select_related('category').order_by('-created_at')
    if not videos.exists():
        return get_dashboard_empty_response()
    
    hero_video = videos.first()
    hero_serializer = VideoListSerializer(hero_video, context={'request': request})
    
    categories_dict = build_categories_dict(videos)
    result_categories = serialize_categories(categories_dict, request)

    return Response({
        'hero_video': hero_serializer.data,
        'categories': result_categories
    }, status=status.HTTP_200_OK)
def get_manifest_path(movie_id, resolution):
    """Get path to HLS manifest file.
    Constructs filesystem path for specific video resolution manifest.
    Returns absolute path to m3u8 playlist file for streaming."""
    return os.path.join(
        settings.MEDIA_ROOT, 'hls', str(movie_id), resolution, 'index.m3u8'
    )


def read_manifest_file(manifest_path):
    """Read and return manifest file content.
    Safely reads HLS manifest with proper error handling.
    Returns m3u8 playlist content as string for HTTP response."""
    if not os.path.exists(manifest_path):
        raise Http404("Video or manifest not found")

    try:
        with open(manifest_path, 'r') as f:
            return f.read()
    except Exception:
        raise Http404("Video or manifest not found")


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def hls_manifest_view(request, movie_id, resolution):
    """GET /api/video/<movie_id>/<resolution>/index.m3u8 - Serve HLS manifest.
    Returns M3U8 playlist file for adaptive streaming playback."""
    get_object_or_404(Video, id=movie_id, hls_processed=True)
    manifest_path = get_manifest_path(movie_id, resolution)
    content = read_manifest_file(manifest_path)

    return HttpResponse(
        content, content_type='application/vnd.apple.mpegurl',
        status=status.HTTP_200_OK
    )


def get_segment_path(movie_id, resolution, segment):
    """Get path to HLS segment file.
    Constructs filesystem path to individual video segment (.ts file).
    Essential for serving chunked video content during streaming playback."""
    return os.path.join(
        settings.MEDIA_ROOT, 'hls', str(movie_id), resolution, segment
    )


def read_segment_file(segment_path):
    """Read and return segment file content.
    Safely reads binary video segment with error handling.
    Optimized for streaming performance with minimal memory usage."""
    if not os.path.exists(segment_path):
        raise Http404("Video or segment not found")

    try:
        with open(segment_path, 'rb') as f:
            return f.read()
    except Exception:
        raise Http404("Video or segment not found")


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def hls_segment_view(request, movie_id, resolution, segment):
    """GET /api/video/<movie_id>/<resolution>/<segment>/ - Serve HLS segment."""
    get_object_or_404(Video, id=movie_id, hls_processed=True)
    segment_path = get_segment_path(movie_id, resolution, segment)
    content = read_segment_file(segment_path)

    return HttpResponse(
        content, content_type='video/MP2T', status=status.HTTP_200_OK
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_thumbnail_view(request, video_id):
    """
    POST /api/video/<video_id>/thumbnail/
    Upload a custom thumbnail for a video.
    """
    try:
        video = get_object_or_404(Video, id=video_id)
        
        from .serializers import ThumbnailUploadSerializer
        serializer = ThumbnailUploadSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                {'error': 'Invalid data', 'details': serializer.errors}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        thumbnail_file = serializer.validated_data['thumbnail']
        
        if video.thumbnail:
            video.thumbnail.delete(save=False)
        
        video.thumbnail = thumbnail_file
        video.save()
        
        from .serializers import VideoListSerializer
        video_serializer = VideoListSerializer(video, context={'request': request})
        
        return Response({
            'message': 'Thumbnail uploaded successfully.',
            'video': video_serializer.data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': f'Upload error: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def regenerate_thumbnail_view(request, video_id):
    """
    POST /api/video/<video_id>/regenerate-thumbnail/
    Regenerate thumbnail for a video from the video file.
    """
    try:
        video = get_object_or_404(Video, id=video_id)
        
        if not video.video_file:
            return Response(
                {'error': 'No video file available.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        from ..utils.core import queue_video_processing
        import django_rq
        
        try:
            queue = django_rq.get_queue('default')
            job = queue.enqueue('video_app.utils.regenerate_thumbnail_job', video.id)
            
            return Response({
                'message': 'Thumbnail regeneration started.',
                'job_id': job.id
            }, status=status.HTTP_202_ACCEPTED)
            
        except Exception as queue_error:
            from ..utils.ffmpeg import generate_video_thumbnail_for_instance
            
            if video.thumbnail:
                video.thumbnail.delete(save=False)
            
            success = generate_video_thumbnail_for_instance(video)
            
            if success:
                from .serializers import VideoListSerializer
                serializer = VideoListSerializer(video, context={'request': request})
                
                return Response({
                    'message': 'Thumbnail regenerated successfully.',
                    'video': serializer.data
                }, status=status.HTTP_200_OK)
            else:
                return Response(
                    {'error': 'Thumbnail generation failed.'}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
    except Exception as e:
        return Response(
            {'error': f'Regeneration error: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def video_status_view(request, video_id):
    """
    GET /api/video/<video_id>/status/
    Get processing status for a video (thumbnail and HLS conversion).
    """
    try:
        video = get_object_or_404(Video, id=video_id)
        
        has_thumbnail = bool(video.thumbnail and video.thumbnail.name)
        thumbnail_url = None
        
        if has_thumbnail:
            try:
                if hasattr(video.thumbnail, 'path') and os.path.exists(video.thumbnail.path):
                    thumbnail_url = request.build_absolute_uri(video.thumbnail.url)
                else:
                    has_thumbnail = False
            except:
                has_thumbnail = False
        
        from ..utils.hls import check_conversion_status
        hls_status = check_conversion_status(video)
        
        return Response({
            'video_id': video.id,
            'title': video.title,
            'has_video_file': bool(video.video_file),
            'thumbnail': {
                'has_thumbnail': has_thumbnail,
                'thumbnail_url': thumbnail_url,
            },
            'hls': {
                'is_processed': hls_status['is_processed'],
                'progress': hls_status['progress'],
                'available_resolutions': hls_status['available_resolutions'],
                'total_resolutions': hls_status['total_resolutions'],
            },
            'created_at': video.created_at,
            'updated_at': video.updated_at
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': f'Status check error: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

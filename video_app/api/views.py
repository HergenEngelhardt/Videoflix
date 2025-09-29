from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.http import HttpResponse, Http404
from django.conf import settings
from django.shortcuts import get_object_or_404
import os

from .serializers import VideoListSerializer
from .permissions import IsAuthenticatedForVideo
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
@permission_classes([IsAuthenticatedForVideo])
def hls_manifest_view(request, movie_id, resolution):
    """GET /api/video/<movie_id>/<resolution>/index.m3u8 - Serve HLS manifest.
    Returns M3U8 playlist file for adaptive streaming playback."""
    video = get_object_or_404(Video, id=movie_id, hls_processed=True)
    manifest_path = get_manifest_path(movie_id, resolution)
    content = read_manifest_file(manifest_path)
    
    return HttpResponse(
        content, content_type='application/vnd.apple.mpegurl',
        status=status.HTTP_200_OK
    )


def get_segment_path(movie_id, resolution, segment):
    """Get path to HLS segment file.
    Constructs filesystem path to individual video segment (.ts file)."""
    return os.path.join(
        settings.MEDIA_ROOT, 'hls', str(movie_id), resolution, segment
    )


def read_segment_file(segment_path):
    """Read and return segment file content.
    Safely reads binary video segment with error handling."""
    if not os.path.exists(segment_path):
        raise Http404("Video or segment not found")
    
    try:
        with open(segment_path, 'rb') as f:
            return f.read()
    except Exception:
        raise Http404("Video or segment not found")


@api_view(['GET'])
@permission_classes([IsAuthenticatedForVideo])
def hls_segment_view(request, movie_id, resolution, segment):
    """GET /api/video/<movie_id>/<resolution>/<segment>/ - Serve HLS segment."""
    video = get_object_or_404(Video, id=movie_id, hls_processed=True)
    segment_path = get_segment_path(movie_id, resolution, segment)
    content = read_segment_file(segment_path)
    
    return HttpResponse(
        content, content_type='video/MP2T', status=status.HTTP_200_OK
    )
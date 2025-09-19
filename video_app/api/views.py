from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.http import HttpResponse, Http404
from django.conf import settings
from django.shortcuts import get_object_or_404
import os

from .serializers import VideoListSerializer, VideoDetailSerializer
from .permissions import IsAuthenticatedForVideo
from ..models import Video


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def video_list_view(request):
    """
    GET /api/video/
    Get list of all available videos.
    """
    videos = Video.objects.select_related('category').all()
    serializer = VideoListSerializer(videos, many=True, context={'request': request})
    
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticatedForVideo])
def hls_manifest_view(request, movie_id, resolution):
    """
    GET /api/video/<int:movie_id>/<str:resolution>/index.m3u8
    Serve HLS manifest file for specific video and resolution.
    """
    video = get_object_or_404(Video, id=movie_id, hls_processed=True)
    
    manifest_path = os.path.join(
        settings.MEDIA_ROOT, 
        'hls', 
        str(movie_id), 
        resolution, 
        'index.m3u8'
    )
    
    if not os.path.exists(manifest_path):
        raise Http404("Video or manifest not found")
    
    try:
        with open(manifest_path, 'r') as f:
            content = f.read()
        
        return HttpResponse(
            content, 
            content_type='application/vnd.apple.mpegurl',
            status=status.HTTP_200_OK
        )
    except Exception:
        raise Http404("Video or manifest not found")


@api_view(['GET'])
@permission_classes([IsAuthenticatedForVideo])
def hls_segment_view(request, movie_id, resolution, segment):
    """
    GET /api/video/<int:movie_id>/<str:resolution>/<str:segment>/
    Serve HLS video segment for specific video and resolution.
    """
    video = get_object_or_404(Video, id=movie_id, hls_processed=True)
    
    segment_path = os.path.join(
        settings.MEDIA_ROOT, 
        'hls', 
        str(movie_id), 
        resolution, 
        segment
    )
    
    if not os.path.exists(segment_path):
        raise Http404("Video or segment not found")
    
    try:
        with open(segment_path, 'rb') as f:
            content = f.read()
        
        return HttpResponse(
            content, 
            content_type='video/MP2T',
            status=status.HTTP_200_OK
        )
    except Exception:
        raise Http404("Video or segment not found")
from django.urls import path
from . import views

urlpatterns = [
    path('', views.video_list_view, name='video_list'),
    path('<int:movie_id>/<str:resolution>/index.m3u8', views.hls_manifest_view, name='hls_manifest'),
    path('<int:movie_id>/<str:resolution>/<str:segment>/', views.hls_segment_view, name='hls_segment'),
]

from django.urls import path
from . import views

urlpatterns = [
    path('', views.video_list_view, name='video_list'),
    path('dashboard/', views.dashboard_view, name='video_dashboard'),
    path('<int:video_id>/thumbnail/', views.upload_thumbnail_view, name='upload_thumbnail'),
    path('<int:video_id>/regenerate-thumbnail/', views.regenerate_thumbnail_view, name='regenerate_thumbnail'),
    path('<int:video_id>/status/', views.video_status_view, name='video_status'),
    path('<int:movie_id>/<str:resolution>/index.m3u8', views.hls_manifest_view, name='hls_manifest'),
    path('<int:movie_id>/<str:resolution>/<str:segment>/', views.hls_segment_view, name='hls_segment'),
]

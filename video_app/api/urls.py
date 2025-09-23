from django.urls import path
from . import views

urlpatterns = [
    path('', views.video_list_view, name='video_list'),
    path('categories/', views.category_list_view, name='category_list'),
    path('category/<int:category_id>/', views.videos_by_category_view, name='videos_by_category'),
    path('<int:movie_id>/', views.video_detail_view, name='video_detail'),
    path('<int:movie_id>/<str:resolution>/index.m3u8', views.hls_manifest_view, name='hls_manifest'),
    path('<int:movie_id>/<str:resolution>/<str:segment>/', views.hls_segment_view, name='hls_segment'),
]
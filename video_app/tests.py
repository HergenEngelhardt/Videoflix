"""
Unit tests for video_app functionality.

This module contains comprehensive tests for video models, utilities,
and API endpoints to ensure proper functionality and data integrity.
"""
import os
import tempfile
from unittest.mock import patch, MagicMock
from django.test import TestCase, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from .models import Video, Category
from .utils import (
    get_resolution_configs, 
    build_ffmpeg_command, 
    get_hls_resolutions,
    cleanup_hls_files,
    get_hls_playlist_url
)

User = get_user_model()


class CategoryModelTest(TestCase):
    """Test cases for Category model."""
    
    def setUp(self):
        """Set up test data."""
        self.category = Category.objects.create(name="Action")
    
    def test_category_creation(self):
        """Test category creation and string representation."""
        self.assertEqual(self.category.name, "Action")
        self.assertEqual(str(self.category), "Action")
        self.assertTrue(self.category.created_at)
    
    def test_category_unique_constraint(self):
        """Test category name uniqueness."""
        with self.assertRaises(Exception):
            Category.objects.create(name="Action")


class VideoModelTest(TestCase):
    """Test cases for Video model."""
    
    def setUp(self):
        """Set up test data."""
        self.category = Category.objects.create(name="Drama")
        self.video = Video.objects.create(
            title="Test Video",
            description="A test video description",
            category=self.category
        )
    
    def test_video_creation(self):
        """Test video creation and basic properties."""
        self.assertEqual(self.video.title, "Test Video")
        self.assertEqual(self.video.description, "A test video description")
        self.assertEqual(self.video.category, self.category)
        self.assertFalse(self.video.hls_processed)
        self.assertIsNone(self.video.hls_path)
    
    def test_video_string_representation(self):
        """Test video string representation."""
        self.assertEqual(str(self.video), "Test Video")
    
    def test_thumbnail_url_property(self):
        """Test thumbnail URL property."""
        # Without thumbnail
        self.assertIsNone(self.video.thumbnail_url)
        
        # With mock thumbnail
        self.video.thumbnail = "thumbnails/test.jpg"
        expected_url = "/media/thumbnails/test.jpg"
        self.assertEqual(self.video.thumbnail_url, expected_url)


class VideoUtilsTest(TestCase):
    """Test cases for video utility functions."""
    
    def test_get_resolution_configs(self):
        """Test resolution configurations."""
        configs = get_resolution_configs()
        self.assertEqual(len(configs), 3)
        
        # Check specific resolution
        resolution_480p = configs[0]
        self.assertEqual(resolution_480p['name'], '480p')
        self.assertEqual(resolution_480p['width'], 854)
        self.assertEqual(resolution_480p['height'], 480)
        self.assertEqual(resolution_480p['bitrate'], '1000k')
    
    def test_build_ffmpeg_command(self):
        """Test FFmpeg command building."""
        resolution = {'name': '720p', 'width': 1280, 'height': 720, 'bitrate': '2500k'}
        video_path = "/test/video.mp4"
        output_path = "/test/output.m3u8"
        res_dir = "/test/720p"
        
        cmd = build_ffmpeg_command(video_path, resolution, output_path, res_dir)
        
        self.assertIn('ffmpeg', cmd)
        self.assertIn(video_path, cmd)
        self.assertIn('scale=1280:720', cmd)
        self.assertIn('2500k', cmd)
    
    @override_settings(MEDIA_ROOT=tempfile.mkdtemp())
    def test_get_hls_resolutions_no_processing(self):
        """Test getting HLS resolutions when video not processed."""
        category = Category.objects.create(name="Test")
        video = Video.objects.create(
            title="Test Video",
            description="Test",
            category=category,
            hls_processed=False
        )
        
        resolutions = get_hls_resolutions(video)
        self.assertEqual(resolutions, [])
    
    @override_settings(MEDIA_ROOT=tempfile.mkdtemp())
    def test_cleanup_hls_files(self):
        """Test HLS files cleanup."""
        category = Category.objects.create(name="Test")
        video = Video.objects.create(
            title="Test Video",
            description="Test",
            category=category,
            hls_path="hls/1/"
        )
        
        # Test cleanup when no files exist
        result = cleanup_hls_files(video)
        self.assertTrue(result)
        
        # Test cleanup when no hls_path
        video.hls_path = None
        result = cleanup_hls_files(video)
        self.assertTrue(result)
    
    def test_get_hls_playlist_url(self):
        """Test HLS playlist URL generation."""
        category = Category.objects.create(name="Test")
        video = Video.objects.create(
            title="Test Video",
            description="Test",
            category=category,
            id=1,
            hls_processed=True
        )
        
        with patch('video_app.utils.get_hls_resolutions') as mock_resolutions:
            mock_resolutions.return_value = ['480p', '720p']
            
            # Test valid resolution
            url = get_hls_playlist_url(video, '720p')
            expected = "/media/hls/1/720p/index.m3u8"
            self.assertEqual(url, expected)
            
            # Test invalid resolution
            url = get_hls_playlist_url(video, '1080p')
            self.assertIsNone(url)


class VideoAPITest(APITestCase):
    """Test cases for Video API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(name="Action")
        self.video = Video.objects.create(
            title="Test Video",
            description="A test video",
            category=self.category,
            hls_processed=True,
            hls_path="hls/1/"
        )
        self.client = APIClient()
    
    def test_video_list_unauthenticated(self):
        """Test video list access without authentication."""
        url = reverse('video-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_video_list_authenticated(self):
        """Test video list access with authentication."""
        self.client.force_authenticate(user=self.user)
        url = reverse('video-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
    
    def test_video_detail(self):
        """Test video detail endpoint."""
        self.client.force_authenticate(user=self.user)
        url = reverse('video-detail', kwargs={'pk': self.video.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], self.video.title)
    
    def test_category_list(self):
        """Test category list endpoint."""
        self.client.force_authenticate(user=self.user)
        url = reverse('category-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) > 0)

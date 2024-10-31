"""
URL mappings for the workout app.
"""
from django.urls import (
    path,
    include,
)

from rest_framework.routers import DefaultRouter

from workout import views


router = DefaultRouter()
router.register(r'workout', views.WorkoutViewSet)
app_name = 'workout'

urlpatterns = [
    path('', include(router.urls)),
    path('workout/<int:workout_id>/comments/',
         views.CommentListCreateView.as_view(), name='workout-comment'),
    path('workout/<int:workout_id>/comments/<int:pk>/',
         views.CommentDetailView.as_view(), name='comment-detail'),
]

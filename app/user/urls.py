from django.urls import path, include
from rest_framework.routers import DefaultRouter
from user import views

app_name = 'user'

router = DefaultRouter()
router.register(r'group', views.GroupViewSet)

urlpatterns = [
    path('create/', views.CreateUserView.as_view(), name='create'),
    path('token/', views.CreateUserTokenView.as_view(), name='token'),
    path('me/', views.ManageUserView.as_view(), name='me'),
    path('info/', views.UserViewSet.as_view(
        {'get': 'get_user_info'}), name='user-info'),
    path('info/upload-image/', views.UserViewSet.as_view(
        {'post': 'upload_image'}), name='upload-image'),
    path('info/profile-picture/',
         views.UserViewSet.as_view({'get': 'get_profile_picture'}),
         name='profile-picture'),
    path('info/delete-account/',
         views.UserViewSet.as_view({'delete': 'delete_account'}),
         name='delete-account'),
    path('', include(router.urls)),
]

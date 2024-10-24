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
    path('', include(router.urls)),
]

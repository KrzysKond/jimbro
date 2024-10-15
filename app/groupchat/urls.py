from django.urls import path
from . import views

urlpatterns = [
    path('group-messages/<int:group_id>/',
         views.GroupMessagesView.as_view(), name='group_messages'),
    path('user-chatrooms/',
         views.GroupListView.as_view(), name='user_chatrooms')
]

from django.urls import path
from rest_framework.authtoken.views import obtain_auth_token
from . import views

urlpatterns = [
    path('tasks/', views.task_list, name='task_list'),
    path('tasks/<int:id>/', views.task_detail, name='task_detail'),
    path('auth/token/', obtain_auth_token, name='api_token_auth'),
    path('analytics/', views.task_analytics, name='task_analytics'),
]

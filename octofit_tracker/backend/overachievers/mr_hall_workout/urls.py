"""
URL configuration for mr_hall_workout project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from fitness_app.views import WeightLogViewSet, AchievementViewSet, NutritionCheckView, WeatherInfoView, UserProfileViewSet, BadgeTierViewSet, PurchasableBadgeViewSet, AwardBadgeView, PurchaseBadgeView
from django.contrib.auth import views as auth_views

router = DefaultRouter()
router.register(r'weight-logs', WeightLogViewSet, basename='weightlog')
router.register(r'achievements', AchievementViewSet, basename='achievement')
router.register(r'profiles', UserProfileViewSet, basename='userprofile')
router.register(r'badge-tiers', BadgeTierViewSet, basename='badgetier')
router.register(r'purchasable-badges', PurchasableBadgeViewSet, basename='purchasablebadge')

urlpatterns = [
    path("admin/", admin.site.urls, name='overachiever_admin'),
    path("accounts/", include("allauth.urls")),  # Include allauth URLs for OAuth
    path('accounts/login/', auth_views.LoginView.as_view(), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('api/', include(router.urls)),
    path('api/nutrition-check/', NutritionCheckView.as_view(), name='nutrition-check'),
    path('api/weather-info/', WeatherInfoView.as_view(), name='weather-info'),
    path('api/award-badge/', AwardBadgeView.as_view(), name='award-badge'),
    path('api/purchase-badge/', PurchaseBadgeView.as_view(), name='purchase-badge'),
]

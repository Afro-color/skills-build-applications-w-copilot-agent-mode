from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
import requests
from .models import WeightLog, Achievement, UserProfile, BadgeTier, PurchasableBadge, DailyBadgeLimit, WeeklyBadgePurchase, Task
from .serializers import WeightLogSerializer, AchievementSerializer, UserProfileSerializer, BadgeTierSerializer, PurchasableBadgeSerializer
from django.http import JsonResponse
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import api_view
from django.db.models import Count

class WeightLogViewSet(viewsets.ModelViewSet):
    queryset = WeightLog.objects.all()
    serializer_class = WeightLogSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class AchievementViewSet(viewsets.ModelViewSet):
    queryset = Achievement.objects.all()
    serializer_class = AchievementSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class UserProfileViewSet(viewsets.ModelViewSet):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class BadgeTierViewSet(viewsets.ModelViewSet):
    queryset = BadgeTier.objects.all()
    serializer_class = BadgeTierSerializer
    permission_classes = [IsAuthenticated]

class PurchasableBadgeViewSet(viewsets.ModelViewSet):
    queryset = PurchasableBadge.objects.all()
    serializer_class = PurchasableBadgeSerializer
    permission_classes = [IsAuthenticated]

class NutritionCheckView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        food_item = request.query_params.get('food', '')
        if not food_item:
            return Response({"error": "Food item is required"}, status=400)

        # Example API call to Edamam (replace with your API key)
        api_url = f"https://api.edamam.com/api/nutrition-data?app_id=YOUR_APP_ID&app_key=YOUR_APP_KEY&ingr={food_item}"
        response = requests.get(api_url)
        if response.status_code == 200:
            return Response(response.json())
        return Response({"error": "Failed to fetch nutrition data"}, status=response.status_code)

class WeatherInfoView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        location = request.query_params.get('location', 'New York')

        # Example API call to OpenWeatherMap (replace with your API key)
        api_url = f"https://api.openweathermap.org/data/2.5/weather?q={location}&appid=YOUR_API_KEY"
        response = requests.get(api_url)
        if response.status_code == 200:
            return Response(response.json())
        return Response({"error": "Failed to fetch weather data"}, status=response.status_code)

class AwardBadgeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        badge_id = request.data.get('badge_id')
        if not badge_id:
            return Response({"error": "Badge ID is required"}, status=400)

        try:
            badge = PurchasableBadge.objects.get(id=badge_id)
        except PurchasableBadge.DoesNotExist:
            return Response({"error": "Badge not found"}, status=404)

        # Check if the badge is in the current season
        if not badge.is_current_season():
            return Response({"error": "Badge is not available in the current season"}, status=400)

        # Check daily badge limit
        daily_limit, created = DailyBadgeLimit.objects.get_or_create(user=request.user, date=now().date())
        if not daily_limit.can_award_badge():
            return Response({"error": "Daily badge limit reached"}, status=400)

        # Award the badge
        daily_limit.increment_badge_count()
        return Response({"message": "Badge awarded successfully!"})

class PurchaseBadgeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        badge_id = request.data.get('badge_id')
        if not badge_id:
            return Response({"error": "Badge ID is required. Did you forget your glasses?"}, status=400)

        try:
            badge = PurchasableBadge.objects.get(id=badge_id)
        except PurchasableBadge.DoesNotExist:
            return Response({"error": "Badge not found. Maybe it went on vacation?"}, status=404)

        # Check weekly badge purchase limit
        if not WeeklyBadgePurchase.can_purchase_badge(request.user):
            return Response({"error": "Weekly badge purchase limit reached. Save some badges for next week!"}, status=400)

        # Record the badge purchase
        WeeklyBadgePurchase.objects.create(user=request.user, badge=badge)
        return Response({"message": f"Badge '{badge.name}' purchased successfully! Enjoy your shiny new badge!"})

class TaskPagination(PageNumberPagination):
    page_size = 10

@api_view(['GET'])
def task_list(request):
    tasks = Task.objects.all()
    paginator = TaskPagination()
    paginated_tasks = paginator.paginate_queryset(tasks, request)
    return paginator.get_paginated_response([{"id": task.id, "name": task.name, "completed": task.completed} for task in paginated_tasks])

def task_detail(request, id):
    # Example response for a single task
    task = {"id": id, "name": f"Task {id}", "completed": False}
    return JsonResponse({"task": task})

@api_view(['GET'])
def task_analytics(request):
    analytics = Task.objects.aggregate(
        completed=Count('id', filter=models.Q(completed=True)),
        pending=Count('id', filter=models.Q(completed=False)),
    )
    return Response(analytics)
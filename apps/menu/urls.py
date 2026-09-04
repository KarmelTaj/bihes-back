from django.urls import path
from rest_framework.routers import DefaultRouter

from .recommendation_views import MenuRecommendationView
from .views import CategoryViewSet, MenuItemViewSet

router = DefaultRouter()
router.register("categories", CategoryViewSet, basename="category")
router.register("menu-items", MenuItemViewSet, basename="menu-item")

urlpatterns = [
    path("recommend/", MenuRecommendationView.as_view(), name="menu-recommend"),
] + router.urls

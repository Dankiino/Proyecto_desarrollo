from django.urls import path

from .views import HealthView, MongoHealthView

urlpatterns = [
    path("health", HealthView.as_view()),
    path("health/mongo", MongoHealthView.as_view()),
]
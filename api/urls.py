from django.urls import path, include
from rest_framework.routers import DefaultRouter
router = DefaultRouter()
urlpatterns = [
    path('auth/', include('users.urls', namespace='users')),
    path('scheduling/', include('scheduling.urls', namespace='scheduling')),
    path('', include(router.urls)),
]

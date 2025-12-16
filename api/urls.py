from django.urls import path, include
from rest_framework.routers import DefaultRouter

router = DefaultRouter()

urlpatterns = [
    path('auth/', include('users.urls', namespace='users')),
    path('', include(router.urls)),
]

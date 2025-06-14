from django.contrib import admin
from django.urls import path, include
from accounts.views import user_profile
from rest_framework import routers
from accounts.api import DailyLogViewSet
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

router = routers.DefaultRouter()
router.register(r'log_drink', DailyLogViewSet, basename='log_drink')


urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('achievements/', include('achievements.urls')),
    path('competitions/', include('competitions.urls')),
    path('api/profile/', user_profile, name='user_profile'),

    path('api/', include(router.urls)),
    path('accounts/', include('accounts.urls')),

    # JWT token endpoints
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
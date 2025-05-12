from django.contrib import admin
from django.urls import path, include
from accounts.views import user_profile
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('achievements/', include('achievements.urls')),
    path('competitions/', include('competitions.urls')),
    path('api/profile/', user_profile, name='user_profile'),

    # JWT token endpoints
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]

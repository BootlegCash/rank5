# myapp/urls.py

from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),

    # 1. Most specific first:
    path(
        'accounts/competitions/',
        include(('competitions.urls', 'competitions'),
                namespace='competitions')
    ),

    # 2. Then the general accounts URLs:
    path('accounts/', include('accounts.urls')),

    # 3. Finally the root redirect:
    path('', RedirectView.as_view(url='accounts/welcome/')),
]

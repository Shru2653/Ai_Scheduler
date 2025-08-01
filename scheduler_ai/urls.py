"""scheduler_ai URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
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
from taskmanager import views as main_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('chatbot/', include('bot.urls')),
    path('', include('taskmanager.urls')),
    path('accounts/', include('accounts.urls')),
    path('scheduler/', include('scheduler.urls')),
    path('process-sync/', include('process_sync.urls', namespace='process_sync')),
]



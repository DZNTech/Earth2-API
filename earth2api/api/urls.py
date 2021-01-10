from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns
from . import views

urlpatterns = [
    path('users/login/', views.login),
    path('users/properties/', views.properties),
    path('users/generate-api-key/',views.get_api_key),
]

urlpatterns = format_suffix_patterns(urlpatterns)
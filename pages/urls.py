from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('about', views.about, name='pages-about'),
    path('terms', views.terms, name='pages-terms'),
    path('privacy', views.privacy, name='pages-privacy'),

]

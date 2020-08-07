from django.urls import path
from . import views

urlpatterns = [
    path('', views.draft,name='draft'),
    path('running_draft/', views.running_draft,name='running_draft'),
    path('continuedraft', views.continuedraft, name='continuedraft'),
    path('mypick', views.mypick, name='mypick'),
    path('complete', views.complete, name='complete'),


    ]

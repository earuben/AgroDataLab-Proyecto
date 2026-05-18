from django.urls import path

from . import views


urlpatterns = [
    path("", views.home, name="home"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("usuarios/", views.users, name="users"),
    path("acerca/", views.about, name="about"),
]

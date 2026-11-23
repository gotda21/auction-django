from django.urls import path
from . import views

urlpatterns = [
    path("", views.lot_list, name="lot_list"),
    path("lot/<int:lot_id>/", views.lot_detail, name="lot_detail"),
    path("profile/", views.profile, name="profile"),
    path("profile/<str:username>/", views.profile, name="user_profile"),
    path("lot/create/", views.lot_create, name="lot_create"),
    path("lot/<int:lot_id>/edit/", views.lot_edit, name="lot_edit"),
    path("notifications/", views.notifications, name="notifications"),
]

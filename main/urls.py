from django.urls import path
from . import views

urlpatterns = [
    path("", views.lot_list, name="lot_list"),
    path("lot/<int:lot_id>/", views.lot_detail, name="lot_detail"),
]

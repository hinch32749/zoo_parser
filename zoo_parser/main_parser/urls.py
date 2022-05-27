from django.urls import path

from .views import ProductListView, index


urlpatterns = [
    path('parser/', index, name="parser"),
    path('', ProductListView.as_view(), name="new")
]
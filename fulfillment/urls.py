from django.urls import path

from fulfillment import views

urlpatterns = [
    path("", views.recommend_page, name="recommend"),
    path("api/recommend/", views.recommend_api, name="api_recommend"),
    path("api/products/", views.products_api, name="api_products"),
    path("api/boxes/", views.boxes_api, name="api_boxes"),
]

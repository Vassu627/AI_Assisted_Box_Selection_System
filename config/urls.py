from django.contrib import admin
from django.urls import include, path

admin.site.site_header = "Box selection"
admin.site.site_title = "Box selection"
admin.site.index_title = "Catalog and orders"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("fulfillment.urls")),
]

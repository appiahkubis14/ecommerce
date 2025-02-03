from django.contrib import admin
from django.http import HttpResponseServerError
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from django.contrib.staticfiles.urls import staticfiles_urlpatterns


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('home.urls')),
    path('product/', include('products.urls')),
    path('accounts/', include('accounts.urls')),
    path("accounts/", include("allauth.urls")),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL,document_root=settings.STATIC_ROOT)
    # urlpatterns += static(settings.STATICFILES_URL,
    #                       view=lambda req: HttpResponseServerError('500: Server Error'))
    # urlpatterns += static(settings.MEDIAFILES_URL,
    #                       view=lambda req: HttpResponseServerError('500: Server Error'))
    


urlpatterns += staticfiles_urlpatterns()

"""
Root URL Router — like app.use() in Express

Express equivalent:
    app.use('/api/trip', tripRoutes);
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/trip/', include('trip.urls')),  # All /api/trip/* goes to trip app
]

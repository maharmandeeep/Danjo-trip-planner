"""
Trip URL Router — like router.post('/plan', controller) in Express

This handles all /api/trip/* endpoints.
"""
from django.urls import path
from .views import PlanTripView

urlpatterns = [
    path('plan', PlanTripView.as_view(), name='plan-trip'),
    # POST /api/trip/plan → PlanTripView
]

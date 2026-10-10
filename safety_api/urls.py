from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView , TokenRefreshView

from .views import (
    UserRegistrationView,
    EmergencyContactView,
    SOSAlertView,
    SOSLocationUpdateView,
)

urlpatterns = [
    path('auth/register/',UserRegistrationView.as_view(),name='register'),
    path('auth/login/',TokenObtainPairView.as_view(),name='token_obtain_pair'),
    path('auth/token/refresh/',TokenRefreshView.as_view(), name='token_refresh'),
    path('contacts/',EmergencyContactView.as_view(),name='contacts'),
    path('contacts/<int:contact_id>/',
         EmergencyContactView.as_view(),
         name='contact-edit'
         ),
    path('sos/',SOSAlertView.as_view(),name='sos'),
    path(
        'sos/<int:alert_id>/location/',
        SOSLocationUpdateView.as_view(),
        name='sos-location'
    )
]
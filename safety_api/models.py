from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.utils import timezone
# Create your models here.

class User(AbstractUser):
    """
    User

    id → primary key.
    email → unique login identifier.
    password → Django-managed password hash, never plain text.
    first_name, last_name, is_active, date_joined → account details and status.
    """
    email = models.EmailField(unique=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email

class EmergencyContact(models.Model):
    """
    EmergencyContact

    id → primary key.
    user_id → FK to User.id; one user can have many contacts.
    name, phone_number → contact details; store the phone number in normalized format.
    relationship → optional label, such as “sister” or “friend”.
    is_verified, priority → verification state and notification order.
    (user_id, phone_number) → unique together, so one user can’t add the same number twice.

    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='emergency_contacts',
    )
    name = models.CharField(max_length=200)
    phone_number = models.CharField(max_length=16)
    relationship = models.CharField(max_length=200 , blank=True)
    is_verified = models.BooleanField(default=False)

    class Meta:
        constraints =( models.UniqueConstraint(
                fields=['user','phone_number'],
                name = 'unique_contact_per_user',
            ),
        )
    def __str__(self):
        return f"{self.name} ({self.phone_number})"


class SOSAlert(models.Model):
    """
    SOSAlert

    id → primary key; consider a UUID if it will appear in API URLs.
    user_id → FK to User.id; one user can have many alerts.
    status → active, resolved, or cancelled.
    started_at, ended_at → alert timestamps.
    """

    STATUS_CHOICES = (
        ('active','Active'),
        ('resolved','Resolved'),
        ('cancelled','Cancelled'),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sos_alerts',
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='active',
    )
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True , blank=True)

    def __str__(self):
        return self.status


class SOSRecipient(models.Model):
    """
    SOSRecipient

    id → primary key.
    alert_id → FK to SOSAlert.id; one alert can notify many recipients.
    contact_id → FK to EmergencyContact.id; identifies the saved contact.
    contact_name, phone_number → snapshots from when the alert was sent, retained if the contact changes later.
    delivery_status, sent_at → notification result and time.
    """
    DELIVERY_STATUS_CHOICES =(
        ('pending','Pending'),
        ('sent','Sent'),
        ('delivered','Delivered'),
        ('failed','Failed'),
    )
    alert = models.ForeignKey(
        'SOSAlert',
        on_delete=models.CASCADE,
        related_name='alert_receipts',
    )
    contact = models.ForeignKey(
        'EmergencyContact',
        on_delete=models.PROTECT,
        related_name='saved_contacts',
    )
    contact_name = models.CharField(max_length=200)
    phone_number = models.CharField(max_length=16)
    delivery_status = models.CharField(
        max_length=10,
        choices=DELIVERY_STATUS_CHOICES,
        default='pending',
    )
    sent_at = models.DateTimeField(null=True , blank=True)

    def __str__(self):
        return self.delivery_status


class SOSLocationUpdate(models.Model):
    """
    SOSLocationUpdate

    id → primary key.
    alert_id → FK to SOSAlert.id; one alert can have many location updates.
    latitude, longitude, accuracy_meters → reported location.
    captured_at, received_at → when the phone recorded it and when the backend received it.
    Keep these updates only during an active SOS, and define how long to retain them afterward.
    """
    alert = models.ForeignKey(
        'SOSAlert',
        on_delete=models.CASCADE,
        related_name= 'location_updates',
    )
    latitude = models.DecimalField(
        max_digits=10 ,
        decimal_places=6, 
        null=True, 
        blank=True
    )
    longitude = models.DecimalField(
        max_digits=10 ,
        decimal_places=6, 
        null=True, 
        blank=True
    )
    accuracy_meters = models.FloatField(blank=True,null=True)
    captured_at = models.DateTimeField(default=timezone.now)
    received_at = models.DateTimeField(default=timezone.now)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(latitude__range=(-90, 90)),
                name='sos_location_latitude_range',
            ),
            models.CheckConstraint(
                condition=models.Q(longitude__range=(-180, 180)),
                name='sos_location_longitude_range',
            ),
            models.CheckConstraint(
                condition=models.Q(accuracy_meters__gte=0),
                name='sos_location_accuracy_nonnegative',
            ),
        ]

    def __str__(self):
        return f"{self.latitude} ({self.longitude})"


class CrimeDataImport(models.Model):
    """
    CrimeDatasetImport

    id → primary key.
    source, dataset_version, coverage_period → identify the NCRB data used.
    imported_at, status → import time and outcome.
    One import can produce many caution areas.
    """
    STATUS_CHOICES = (
        ('running','Running'),
        ('success','Success'),
        ('pending','Pending'),
        ('failed','Failed'),
    )


    source = models.CharField(max_length=200)
    dataset_version = models.CharField(max_length=200)
    coverage_period = models.CharField(max_length=200)
    imported_at = models.DateTimeField(null=True , blank=True)
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='running'
    )
    
    def __str__(self):
        return self.status

class CautionArea(models.Model):
    """
    CautionArea

    id → primary key.
    dataset_import_id → FK to CrimeDatasetImport.id.
    center_latitude, center_longitude, radius_meters → area represented as a circle for V1.
    crime_category, incident_count, risk_score → aggregated area summary, not personal incident details.
    updated_at → when this area’s summary was calculated.
    """
    dataset_import = models.ForeignKey(
        'CrimeDataImport',
        on_delete=models.CASCADE,
        related_name='caution_areas'
    )

    centre_latitude = models.DecimalField(
        max_digits=10 ,
        decimal_places=6, 
        null=True, 
        blank=True
        )
    centre_longitude = models.DecimalField(
         max_digits=10 ,
        decimal_places=6, 
        null=True, 
        blank=True
    )
    radius_meters = models.FloatField(blank=True,null=True)
    crime_category = models.CharField(max_length=200)
    incident_count = models.PositiveIntegerField(default=0)
    risk_score = models.PositiveSmallIntegerField(default=0)
    updated_at = models.DateTimeField(null=True ,blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(centre_latitude__range=(-90, 90)),
                name='caution_area_latitude_range',
            ),
            models.CheckConstraint(
                condition=models.Q(centre_longitude__range=(-180, 180)),
                name='caution_area_longitude_range',
            ),
            models.CheckConstraint(
                condition=models.Q(risk_score__range=(0, 100)),
                name='caution_area_risk_score_range',
            ),
            models.CheckConstraint(
                condition=models.Q(radius_meters__gt=0),
                name='caution_area_radius_positive',
            ),
        ]

    def __str__(self):
        return f"{self.crime_category} ({self.risk_score})"

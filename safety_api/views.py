from multiprocessing import context
from urllib import request

from django.db.models.deletion import ProtectedError
from rest_framework import status
from django.contrib.auth.models import AbstractUser
from django.db.migrations import serializer
from django.db.models import Model
from django.shortcuts import render, get_object_or_404
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import SOSAlert , EmergencyContact
from .serializers import UserRegistrationSerializer , EmergencyContactSerializer , SOSAlertSerializer , SOSLocationUpdateSerializer
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny

class UserRegistrationView(APIView):
    permission_classes = [AllowAny]
    def post(self,request):
        serializer = UserRegistrationSerializer(data = request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        return Response(
            {'id':user.id , 'username':user.username,'email':user.email},
            status=status.HTTP_201_CREATED,
        )

class EmergencyContactView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self,request):
        contact = EmergencyContact.objects.filter(user=request.user)
        serializer = EmergencyContactSerializer(contact,many=True)
        return Response(serializer.data)

    def post(self,request):
        serializer = EmergencyContactSerializer(
            data = request.data,
            context = {'request':request},
        )
        serializer.is_valid(raise_exception=True)
        contact = serializer.save()

        return Response(
            EmergencyContactSerializer(contact).data,
            status = status.HTTP_201_CREATED,
        )

    def put(self,request,contact_id):
        contact = get_object_or_404(
            EmergencyContact,
            id = contact_id,
            user = request.user,
        )
        serializer = EmergencyContactSerializer(
            contact,
            data = request.data,
            context = {'request':request},
        )
        serializer.is_valid(raise_exception=True)
        contact = serializer.save()
        return Response(EmergencyContactSerializer(contact).data)

    def delete(self,request,contact_id):
        contact = get_object_or_404(
            EmergencyContact,
            id = contact_id,
            user = request.user,
        )
        try:
            contact.delete()
        except ProtectedError:
            return Response(
                {'detail':'This contact is attached to an active SOS record and cannot be deleted.'},
                status= status.HTTP_409_CONFLICT
            )

class SOSAlertView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self ,request):
        serializer = SOSAlertSerializer(
            data = request.data ,
            context = {'request':request}
        )
        serializer.is_valid(raise_exception=True)
        sos_alert = serializer.save()

        return Response(
            SOSAlertSerializer(sos_alert).data,
            status = status.HTTP_201_CREATED,
        )

class SOSLocationUpdateView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self,request,alert_id):
        sos_alert = get_object_or_404(
            SOSAlert,
            id = alert_id,
            user = request.user,
        )
        if sos_alert.status != 'active':
            return Response(
                {'detail':'Location update are accepted only for active SOS alerts.'},
                status = status.HTTP_400_BAD_REQUEST,
            )
        serializer = SOSLocationUpdateSerializer(
            data = request.data
        )
        serializer.is_valid(raise_exception=True)
        location_update = serializer.save(alert = sos_alert)

        return Response(
                SOSLocationUpdateSerializer(location_update).data,
                status=status.HTTP_201_CREATED,
            )


from django.utils import timezone
from wsgiref import validate

from rest_framework import serializers
from .models import User , EmergencyContact , SOSAlert , SOSLocationUpdate
class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    password_confirmation = serializers.CharField(write_only=True)
    def validate(self,attrs):
        """

        attrs -> Gets all the attributes for that class or model i.e (username , email , password etc.)
        for this class

        """
        if attrs['password'] != attrs['password_confirmation']:
            raise serializers.ValidationError({'password':'Password fields must match.'})
        return attrs
    def create(self,validated_data):
        """

        validated_data -> Data received after checking if all the parameters of it are
        valid and clean.

        validated_data.pop('password_confirmation') -> Removed password_confirmation field
        as the user doesn't have a defined column to hold it.

        .set_password() -> AbstractBaseUser method to set password in the user password column
        a valid one.

        .save() -> Directly hits the database for storing the data in the password column and the
        exact row of it.

        .save() -> Saves the change that is made in the database.

        """
        validated_data.pop('password_confirmation')
        user = User.objects.create(
            username= validated_data['username'],
            email= validated_data['email']
        )
        user.set_password(validated_data['password'])
        user.save()
        return user
    class Meta:
        model = User
        fields = ('username','email','password','password_confirmation')

class EmergencyContactSerializer(serializers.ModelSerializer):
    relationship = serializers.CharField(required=False ,allow_blank=True)

    def validate(self, attrs):
        if len(attrs['name']) == 0 or len(attrs['name']) == 1 :
            raise serializers.ValidationError({'name':'Name cant be empty or single character.'})
        elif len(attrs['phone_number']) < 10 :
            raise serializers.ValidationError({'phone_number':'Phone number is not valid.'})
        return attrs
    def create(self, validated_data):
        user = self.context['request'].user
        contact = EmergencyContact.objects.create(
            user = user,
            name = validated_data['name'],
            phone_number= validated_data['phone_number'],
            relationship = validated_data.get('relationship' , ''),
        )
        return contact

    class Meta:
        model = EmergencyContact
        fields = ('id','name','phone_number','relationship',)
        read_only_fields = ('id',)

class SOSAlertSerializer(serializers.ModelSerializer):
    def create(self, validated_data):
        user = self.context['request'].user
        sos_alert = SOSAlert.objects.create(
            user = user,
            **validated_data,
        )
        return sos_alert
    def update(self, instance, validated_data):
        if 'status' in validated_data:
            new_status = validated_data['status']
        else:
            new_status = instance.status

        if new_status in ['resolved','cancelled'] and instance.status == 'active' :
            instance.ended_at = timezone.now()

        instance.status = new_status
        instance.save()

        return instance

    class Meta:
        model = SOSAlert
        fields = ('id','status','started_at','ended_at')
        read_only_fields = fields

class SOSLocationUpdateSerializer(serializers.ModelSerializer):
    def validate(self, attrs):
        latitude = attrs['latitude']
        longitude = attrs['longitude']

        if latitude > 90 or latitude < -90:
            raise serializers.ValidationError({'latitude':'Latitude coordinate not valid.'})
        elif longitude > 180 or longitude < -180 :
            raise serializers.ValidationError({'longitude':'Longitude coordinate not valid'})

        return attrs

    def create(self, validated_data):
        location_update = SOSLocationUpdate.objects.create(
            alert = validated_data['alert'],
            latitude = validated_data['latitude'],
            longitude = validated_data['longitude'],
            accuracy_meters = validated_data.get('accuracy_meters'),
            captured_at = validated_data.get('captured_at',timezone.now()),
            received_at = timezone.now()
        )
        return location_update
    class Meta:
        model = SOSLocationUpdate
        fields = ('id','latitude','longitude','accuracy_meters','captured_at','received_at')
        read_only_fields = ('id',)

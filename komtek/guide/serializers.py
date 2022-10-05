from rest_framework import serializers

from guide.models import Guide, GuideElement


class GuideSerializer(serializers.ModelSerializer):

    class Meta:
        model = Guide
        fields = '__all__'


class GuideElementSerializer(serializers.ModelSerializer):

    class Meta:
        model = GuideElement
        fields = '__all__'

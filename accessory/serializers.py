from rest_framework import serializers
from .models import OrgAttach

class OrgAttachSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrgAttach
        fields = '__all__'

    def to_representation(self, instance):
        # 自定义返回格式
        data = super().to_representation(instance)
        # 添加额外信息
        data['url'] = f"/media/{instance.file.name}"
        return data
from bhr.models import WhitelistEntry, Block
from rest_framework import serializers

class WhitelistEntrySerializer(serializers.ModelSerializer):
    who = serializers.SlugField(read_only=True)
    added = serializers.SlugField(read_only=True)
    class Meta:
        model = WhitelistEntry
        fields = ('cidr', 'who', 'why', 'added')

class BlockSerializer(serializers.HyperlinkedModelSerializer):
    who = serializers.SlugField(read_only=True)
    added = serializers.SlugField(read_only=True)
    class Meta:
        model = Block
        fields = fields = ('url', 'cidr', 'why', 'added', 'unblock_at', 'skip_whitelist')

class BlockRequestSerializer(serializers.Serializer):
    cidr = serializers.CharField(max_length=20)
    source = serializers.CharField(max_length=30)
    why = serializers.CharField()
    duration = serializers.IntegerField(required=False)
    unblock_at = serializers.DateTimeField(required=False)

    def validate(self, attrs):
        if attrs.get('duration') and attrs.get('unblock_at'):
            raise serializers.ValidationError("Specify only one of duration and unblock_at")
        return attrs

class SetBlockedSerializer(serializers.Serializer):
    ident = serializers.CharField()

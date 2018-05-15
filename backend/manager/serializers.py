from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from .models import Crawler


class TableSerializer(serializers.Serializer):
    table_name = serializers.CharField(read_only=True)
    count = serializers.IntegerField(read_only=True)
    tables = serializers.MultipleChoiceField(choices=[], write_only=True)

    def __init__(self, *args, **kwargs):
        tables_choices = kwargs.pop('tables_choices', [])
        super(TableSerializer, self).__init__(*args, **kwargs)
        self.fields['tables'].choices = tables_choices


class CrawlerSerializer(serializers.ModelSerializer):
    status = serializers.ReadOnlyField()

    class Meta:
        model = Crawler
        fields = '__all__'
        read_only_fields = ('status', 'cancel_flag')

    def validate(self, data):
        request = self.context.get('request')
        if request.method == 'POST':
            if Crawler.objects.filter(status__startswith='creating').exists() or Crawler.objects.filter(status__startswith='running').exists():
                raise ValidationError('There already exists active crawler')

        return data


class CrawlerDetailSerializer(CrawlerSerializer):
    year = serializers.ReadOnlyField()
    semester = serializers.ReadOnlyField()

import threading

from django.apps import apps
from django.http import QueryDict
from rest_framework import generics
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from .models import Crawler
from .serializers import CrawlerSerializer, CrawlerDetailSerializer, TableSerializer

from .crawler import run


class TableView(generics.ListCreateAPIView):
    """
    List # of instances for each table(model)
    or Delete all instances for each table at once.
    """
    serializer_class = TableSerializer
    permission_classes = (IsAdminUser,)
    app_labels = ('ttrs', 'manager')

    def get_models(self):
        models = []
        for app_label in self.app_labels:
            for model in apps.get_app_config(app_label).get_models():
                models.append(model)
        return models

    def get_queryset(self):
        tables = []
        for model in self.get_models():
            tables.append(dict(table_name=model.__name__, count=model.objects.count()))
        return tables

    def get_serializer(self, *args, **kwargs):
        serializer_class = self.get_serializer_class()
        kwargs['context'] = self.get_serializer_context()
        kwargs['tables_choices'] = [(model.__name__, model.__name__) for model in self.get_models()]
        return serializer_class(*args, **kwargs)

    def create(self, request, *args, **kwargs):
        if isinstance(request.data, QueryDict):
            names = request.data.getlist('tables', [])
        else:
            names = request.data['tables']
            if names is None:
                names = []
        models = list(filter(lambda x: x.__name__ in names, self.get_models()))
        for model in models:
            model.objects.all().delete()
        return Response(self.get_queryset())


class CrawlerList(generics.ListCreateAPIView):
    queryset = Crawler.objects.all()
    serializer_class = CrawlerSerializer
    permission_classes = (IsAdminUser, )

    def perform_create(self, serializer):
        crawler = serializer.save(status='creating')
        thread = threading.Thread(target=run, args=(crawler,))
        thread.start()


class CrawlerDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Crawler.objects.all()
    serializer_class = CrawlerDetailSerializer
    permission_classes = (IsAdminUser, )

    def perform_update(self, serializer):
        serializer.save(cancel_flag=True)

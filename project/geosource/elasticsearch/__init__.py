from django.conf import settings
from elasticsearch import Elasticsearch


class ESMixin:
    @classmethod
    def get_client(cls):
        return Elasticsearch(
            settings.ES_URL,
            max_retries=10,
            retry_on_timeout=True,
            timeout=30,
        )

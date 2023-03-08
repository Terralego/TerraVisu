from elasticsearch import Elasticsearch


class ESMixin:
    @classmethod
    def get_client(cls):
        return Elasticsearch(
            "http://elasticsearch:9200",
            max_retries=10,
            retry_on_timeout=True,
            timeout=30,
        )

from rest_framework.pagination import LimitOffsetPagination

class FeaturePagination(LimitOffsetPagination):
    default_limit = 100 # ça va dépendre des cas d'usage mais 100 semble OK pour le moment
    max_limit = 100000 # pas de sens au delà, autant juste ajouter un offset et récupérer les 100 000 suivants
    
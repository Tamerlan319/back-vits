from django.core.cache import cache
from django.conf import settings

class CacheListRetrieveMixin:
    cache_timeout = 60 * 15  # 15 минут

    def list(self, request, *args, **kwargs):
        if settings.CACHE_ENABLED:
            cache_key = self.get_cache_key('list', request)
            cached_data = cache.get(cache_key)
            if cached_data is not None:
                from rest_framework.response import Response
                return Response(cached_data)

        response = super().list(request, *args, **kwargs)

        if settings.CACHE_ENABLED:
            cache.set(cache_key, response.data, self.cache_timeout)

        return response

    def retrieve(self, request, *args, **kwargs):
        if settings.CACHE_ENABLED:
            cache_key = self.get_cache_key('detail', request, kwargs.get('pk'))
            cached_data = cache.get(cache_key)
            if cached_data is not None:
                from rest_framework.response import Response
                return Response(cached_data)

        response = super().retrieve(request, *args, **kwargs)

        if settings.CACHE_ENABLED:
            cache.set(cache_key, response.data, self.cache_timeout)

        return response

    def get_cache_key(self, view_type, request, pk=None):
        params = request.query_params.urlencode()
        if view_type == 'list':
            return f"{request.path}?{params}"
        return f"{request.path}_{pk}?{params}"
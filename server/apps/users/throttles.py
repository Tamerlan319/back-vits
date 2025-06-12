from rest_framework.throttling import SimpleRateThrottle

class RegisterRateThrottle(SimpleRateThrottle):
    scope = 'register'

    def get_cache_key(self, request, view):
        return self.get_ident(request)  # идентификатор — IP-адрес
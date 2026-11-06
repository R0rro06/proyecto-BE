"""Keep optional cookies disabled until the visitor accepts them."""


class CookieConsentMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.COOKIES.get('consentimiento_cookies') != 'aceptar':
            request.COOKIES.pop('lectura_ampliada', None)
            request.COOKIES.pop('tema', None)
        response = self.get_response(request)
        if request.COOKIES.get('consentimiento_cookies') != 'aceptar':
            response.delete_cookie('lectura_ampliada', samesite='Lax')
            response.delete_cookie('tema', samesite='Lax')
        return response

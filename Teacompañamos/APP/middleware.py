"""Protecciones HTTP y preferencias de cookies de la aplicación."""

from django.http import HttpResponse


MAX_FORM_BODY_BYTES = 256 * 1024


class FormBodyLimitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method in {'POST', 'PUT', 'PATCH'}:
            length = request.META.get('CONTENT_LENGTH', '')
            if (not isinstance(length, str) or len(length) > 6 or
                    not length.isascii() or not length.isdecimal() or
                    int(length) > MAX_FORM_BODY_BYTES):
                return HttpResponse('Formulario demasiado grande o sin tamaño declarado.', status=413)
        return self.get_response(request)


class CookieConsentMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        legacy_reading = request.COOKIES.pop('lectura_ampliada', None) is not None
        if request.COOKIES.get('consentimiento_cookies') != 'aceptar':
            request.COOKIES.pop('tema', None)
        response = self.get_response(request)
        if legacy_reading:
            response.delete_cookie('lectura_ampliada', samesite='Lax')
        if request.COOKIES.get('consentimiento_cookies') != 'aceptar':
            response.delete_cookie('tema', samesite='Lax')
        return response

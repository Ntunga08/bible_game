from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if isinstance(exc, (TokenError, InvalidToken)):
        return Response({
            'detail': 'Your session has expired. Please log in again.',
            'code': 'token_not_valid',
            'redirect': True
        }, status=status.HTTP_401_UNAUTHORIZED)
    if response is not None and response.status_code == 401:
        response.data['detail'] = 'Authentication credentials were not provided or are invalid.'
        response.data['redirect'] = True
    return response
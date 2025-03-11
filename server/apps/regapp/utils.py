from itsdangerous import URLSafeTimedSerializer
from django.conf import settings

def generate_confirmation_token(email):
    serializer = URLSafeTimedSerializer(settings.SECRET_KEY)
    return serializer.dumps(email, salt='email-confirmation')

def confirm_token(token, expiration=3600):
    serializer = URLSafeTimedSerializer(settings.SECRET_KEY)
    try:
        email = serializer.loads(
            token,
            salt='email-confirmation',
            max_age=expiration
        )
    except:
        return False
    return email
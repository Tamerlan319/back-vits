from django.contrib import admin
from .models import Audience, Characteristic, AudienceImage

admin.site.register(Audience)
admin.site.register(Characteristic)
admin.site.register(AudienceImage)
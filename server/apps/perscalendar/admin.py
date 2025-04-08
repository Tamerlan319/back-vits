from django.contrib import admin
from .models import Event, UserEvent

admin.site.register(Event)
admin.site.register(UserEvent)
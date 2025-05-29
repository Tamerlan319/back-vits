from django.contrib import admin
from .models import Application, ApplicationAttachment, ApplicationStatusLog

admin.site.register(Application)
admin.site.register(ApplicationAttachment)
admin.site.register(ApplicationStatusLog)
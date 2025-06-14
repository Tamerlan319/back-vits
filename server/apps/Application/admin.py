from django.contrib import admin
from .models import Application, ApplicationAttachment, ApplicationStatusLog, ApplicationType

admin.site.register(Application)
admin.site.register(ApplicationAttachment)
admin.site.register(ApplicationStatusLog)
admin.site.register(ApplicationType)
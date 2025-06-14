from django.contrib import admin
from .models import Banner, Achievement, Review, OrganizationDocument, VideoContent

admin.site.register(Banner)
admin.site.register(Achievement)
admin.site.register(Review)
admin.site.register(OrganizationDocument)
admin.site.register(VideoContent)
from django.contrib import admin
from .models import Department, EducationLevel, Program, PartnerCompany, ProgramFeature

admin.site.register(Department)
admin.site.register(EducationLevel)
admin.site.register(Program)
admin.site.register(PartnerCompany)
admin.site.register(ProgramFeature)
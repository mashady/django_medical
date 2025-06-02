from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import *

class UserAdmin(BaseUserAdmin):
    list_display = ('id', 'username', 'email', 'role', 'is_active')
    list_filter = ('role', 'is_active')
    fieldsets = BaseUserAdmin.fieldsets + (
        (None, {'fields': ('role',)}),
    )

admin.site.register(User, UserAdmin)
admin.site.register(Specialty)
admin.site.register(DoctorProfile)
admin.site.register(PatientProfile)
admin.site.register(DoctorAvailability)
admin.site.register(Appointment)
admin.site.register(Notification)

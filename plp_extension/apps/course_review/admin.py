# coding: utf-8

from django.contrib import admin
from plp.custom_admin import admin_site, ModelAdminWithReadOnly
from plp_extension.apps.course_review.models import CourseFeedbackSettings


@admin.register(CourseFeedbackSettings, site=admin_site)
class CourseFeedbackSettingsAdmin(ModelAdminWithReadOnly):
    list_display = ('disable_ratings', 'disable_feedbacks')

    def has_add_permission(self, request):
        """
        Следим за тем, чтобы в системе было не больше 1 объекта CourseFeedbackSettings
        """
        base_perm = super(CourseFeedbackSettingsAdmin, self).has_add_permission(request)
        if base_perm:
            if not CourseFeedbackSettings.objects.exists():
                return True
        return False

# encoding: utf-8

from django import template
from django.contrib.admin.templatetags.admin_modify import submit_row

register = template.Library()

register.inclusion_tag('pse/plp/submit_line_non_staff.html', takes_context=True, name='submit_row_non_staff')(submit_row)

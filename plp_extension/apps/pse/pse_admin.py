# coding: utf-8

from django.apps import apps
from django.contrib.admin import AdminSite, helpers
from django.contrib.admin.options import IncorrectLookupParameters, ModelAdmin
from django.contrib.auth import get_permission_codename
from django.contrib import messages
from django.core.urlresolvers import NoReverseMatch, reverse
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.template.response import SimpleTemplateResponse, TemplateResponse
from django.utils import six
from django.utils.text import capfirst
from django.utils.translation import ugettext as _, ungettext
from django.utils.encoding import force_text
from django.views.decorators.cache import never_cache
from django.conf import settings
from django.shortcuts import redirect
from plp.custom_admin import SimpleHistoryAdminSaveInitial

from plp.models import CourseSessionAccessRole


class AdminSiteWithReadOnly(AdminSite):
    """
    Замена стандартного AdminSite с целью корректной обработки view permission
    """
    def has_permission(self, request):
        """
        Returns True if the given HttpRequest has permission to view
        *at least one* page in the admin site.
        """
        has_role = request.user.is_authenticated() and CourseSessionAccessRole.objects.filter(user=request.user).exists()
        return request.user.is_staff or has_role

    def register(self, model_or_iterable, admin_class=None, **options):
        if not hasattr(model_or_iterable, '__iter__'):
            model_or_iterable = [model_or_iterable]
        for model in model_or_iterable:
            if not admin_class:
                adm = ModelAdminWithReadOnly
            else:
                adm = admin_class
            if hasattr(model._meta, 'simple_history_manager_attribute'):

                class Klass(SimpleHistoryAdminSaveInitial, adm):
                    pass

                adm = Klass
            super(AdminSiteWithReadOnly, self).register(model, adm, **options)

    @never_cache
    def login(self, request, extra_context=None):
        if request.GET.get('next', '').startswith('/pse'):
            return redirect('%s?next=%s' % (settings.LOGIN_URL, request.path))
        return super(AdminSiteWithReadOnly, self).login(request, extra_context)

    @never_cache
    def index(self, request, extra_context=None):
        app_dict = {}
        for model, model_admin in self._registry.items():
            app_label = model._meta.app_label
            has_module_perms = model_admin.has_module_permission(request)

            if has_module_perms:
                perms = model_admin.get_model_perms(request)

                if True in perms.values():
                    # обработка view permission
                    if perms.values().count(True) == 1 and 'view' in perms and not perms['view']:
                        continue
                    info = (app_label, model._meta.model_name)
                    model_dict = {
                        'name': capfirst(model._meta.verbose_name_plural),
                        'object_name': model._meta.object_name,
                        'perms': perms,
                        'view_permission': True,
                    }
                    try:
                        model_dict['view_url'] = reverse('admin:%s_%s_changelist' % info, current_app=self.name)
                    except NoReverseMatch:
                        pass
                    if perms.get('change', False):
                        try:
                            model_dict['admin_url'] = reverse('admin:%s_%s_changelist' % info, current_app=self.name)
                        except NoReverseMatch:
                            pass
                    if perms.get('add', False):
                        try:
                            model_dict['add_url'] = reverse('admin:%s_%s_add' % info, current_app=self.name)
                        except NoReverseMatch:
                            pass
                    if app_label in app_dict:
                        app_dict[app_label]['models'].append(model_dict)
                    else:
                        app_dict[app_label] = {
                            'name': apps.get_app_config(app_label).verbose_name,
                            'app_label': app_label,
                            'app_url': reverse(
                                'admin:app_list',
                                kwargs={'app_label': app_label},
                                current_app=self.name,
                            ),
                            'has_module_perms': has_module_perms,
                            'models': [model_dict],
                        }

        app_list = list(six.itervalues(app_dict))
        app_list.sort(key=lambda x: x['name'].lower())

        for app in app_list:
            app['models'].sort(key=lambda x: x['name'])

        context = dict(
            self.each_context(request),
            title=self.index_title,
            app_list=app_list,
        )
        context.update(extra_context or {})

        request.current_app = self.name

        return TemplateResponse(request, self.index_template or
                                'pse/index.html', context)


admin_site = AdminSiteWithReadOnly('pse')


class ModelAdminWithReadOnly(ModelAdmin):
    """
    Класс, обрабатывающий view permission
    """

    MODELS_WITH_SPECIAL_PERMISSIONS = ['course']

    def get_model_perms(self, request):
        perms = super(ModelAdminWithReadOnly, self).get_model_perms(request)
        perms['view'] = self.has_view_permission(request)
        perms['add'] = False
        perms['delete'] = False
        return perms

    def has_view_permission(self, request):
        opts = self.opts
        codename = get_permission_codename('view', opts)
        if opts.model_name in self.MODELS_WITH_SPECIAL_PERMISSIONS:
            return True
        return request.user.has_perm("%s.%s" % (opts.app_label, codename))

    def has_change_permission(self, request, obj=None):
        opts = self.opts
        codename = get_permission_codename('change', opts)
        if opts.model_name in self.MODELS_WITH_SPECIAL_PERMISSIONS:
            return True
        return request.user.has_perm("%s.%s" % (opts.app_label, codename))

    def check_permissions(self, request):
        if not self.has_change_permission(request, None) and not self.has_view_permission(request):
            raise PermissionDenied

    def has_module_permission(self, request):
        if self.opts.model_name in self.MODELS_WITH_SPECIAL_PERMISSIONS:
            return True
        return False

    def get_queryset(self, request):
        qs = super(ModelAdminWithReadOnly, self).get_queryset(request)
        if request.user.is_staff:
            return qs
        if qs.count() == 0:
            return qs
        model_name = qs.first().__class__.__name__.lower()
        if model_name not in self.MODELS_WITH_SPECIAL_PERMISSIONS:
            return qs
        roles = CourseSessionAccessRole.objects.filter(user=request.user)
        list_of_ids = []
        if model_name == 'coursesession' and 'coursesession' in self.MODELS_WITH_SPECIAL_PERMISSIONS:
            for role in roles:
                org, course, session = role.course_id.split('+')
                list_of_ids.extend(qs.filter(slug=session, course__slug=course, course__university__slug=org).values_list('id', flat=True))
            list_of_ids = list(set(list_of_ids))
            qs = qs.filter(pk__in=list_of_ids)
        if model_name == 'course' and 'course' in self.MODELS_WITH_SPECIAL_PERMISSIONS:
            for role in roles:
                org, course, session = role.course_id.split('+')
                list_of_ids.extend(qs.filter(slug=course, university__slug=org).values_list('id', flat=True))
            list_of_ids = list(set(list_of_ids))
            qs = qs.filter(pk__in=list_of_ids)
        return qs

    def changelist_view(self, request, extra_context=None):
        from django.contrib.admin.views.main import ERROR_FLAG
        opts = self.model._meta
        app_label = opts.app_label
        self.check_permissions(request)

        list_display = self.get_list_display(request)
        list_display_links = self.get_list_display_links(request, list_display)
        list_filter = self.get_list_filter(request)
        search_fields = self.get_search_fields(request)

        actions = self.get_actions(request)
        if actions:
            list_display = ['action_checkbox'] + list(list_display)

        ChangeList = self.get_changelist(request)
        try:
            cl = ChangeList(request, self.model, list_display,
                list_display_links, list_filter, self.date_hierarchy,
                search_fields, self.list_select_related, self.list_per_page,
                self.list_max_show_all, self.list_editable, self)

        except IncorrectLookupParameters:
            if ERROR_FLAG in request.GET.keys():
                return SimpleTemplateResponse('admin/invalid_setup.html', {
                    'title': _('Database error'),
                })
            return HttpResponseRedirect(request.path + '?' + ERROR_FLAG + '=1')

        action_failed = False
        selected = request.POST.getlist(helpers.ACTION_CHECKBOX_NAME)

        if (actions and request.method == 'POST' and
                'index' in request.POST and '_save' not in request.POST):
            if selected:
                response = self.response_action(request, queryset=cl.get_queryset(request))
                if response:
                    return response
                else:
                    action_failed = True
            else:
                msg = _("Items must be selected in order to perform "
                        "actions on them. No items have been changed.")
                self.message_user(request, msg, messages.WARNING)
                action_failed = True

        if (actions and request.method == 'POST' and
                helpers.ACTION_CHECKBOX_NAME in request.POST and
                'index' not in request.POST and '_save' not in request.POST):
            if selected:
                response = self.response_action(request, queryset=cl.get_queryset(request))
                if response:
                    return response
                else:
                    action_failed = True

        formset = cl.formset = None

        if (request.method == "POST" and cl.list_editable and
                '_save' in request.POST and not action_failed):
            FormSet = self.get_changelist_formset(request)
            formset = cl.formset = FormSet(request.POST, request.FILES, queryset=cl.result_list)
            if formset.is_valid():
                changecount = 0
                for form in formset.forms:
                    if form.has_changed():
                        obj = self.save_form(request, form, change=True)
                        self.save_model(request, obj, form, change=True)
                        self.save_related(request, form, formsets=[], change=True)
                        change_msg = self.construct_change_message(request, form, None)
                        self.log_change(request, obj, change_msg)
                        changecount += 1

                if changecount:
                    if changecount == 1:
                        name = force_text(opts.verbose_name)
                    else:
                        name = force_text(opts.verbose_name_plural)
                    msg = ungettext("%(count)s %(name)s was changed successfully.",
                                    "%(count)s %(name)s were changed successfully.",
                                    changecount) % {'count': changecount,
                                                    'name': name,
                                                    'obj': force_text(obj)}
                    self.message_user(request, msg, messages.SUCCESS)

                return HttpResponseRedirect(request.get_full_path())

        elif cl.list_editable:
            FormSet = self.get_changelist_formset(request)
            formset = cl.formset = FormSet(queryset=cl.result_list)

        if formset:
            media = self.media + formset.media
        else:
            media = self.media

        if actions:
            action_form = self.action_form(auto_id=None)
            action_form.fields['action'].choices = self.get_action_choices(request)
        else:
            action_form = None

        selection_note_all = ungettext('%(total_count)s selected',
            'All %(total_count)s selected', cl.result_count)

        context = dict(
            self.admin_site.each_context(request),
            module_name=force_text(opts.verbose_name_plural),
            selection_note=_('0 of %(cnt)s selected') % {'cnt': len(cl.result_list)},
            selection_note_all=selection_note_all % {'total_count': cl.result_count},
            title=cl.title,
            is_popup=cl.is_popup,
            to_field=cl.to_field,
            cl=cl,
            media=media,
            has_add_permission=self.has_add_permission(request),
            opts=cl.opts,
            action_form=action_form,
            actions_on_top=self.actions_on_top,
            actions_on_bottom=self.actions_on_bottom,
            actions_selection_counter=self.actions_selection_counter,
            preserved_filters=self.get_preserved_filters(request),
        )
        context.update(extra_context or {})

        request.current_app = self.admin_site.name

        return TemplateResponse(request, self.change_list_template or [
            'pse/%s/%s/change_list.html' % (app_label, opts.model_name),
            'pse/%s/change_list.html' % app_label,
            'pse/change_list.html'
        ], context)

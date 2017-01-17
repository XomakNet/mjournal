from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.http import Http404
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.views.generic import DeleteView
from django.views.generic import FormView
from django.views.generic import RedirectView
from django.views.generic import TemplateView
from django.views.generic.list import ListView

from main.forms import EventForm
from main.models import MaintenanceEvent, MaintenanceObject, MaintenanceType, MaintenanceLink


@method_decorator(login_required, name='dispatch')
class MainView(RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        return reverse('main.dashboard')


@method_decorator(login_required, name='dispatch')
class MaintenanceObjectSummary(TemplateView):
    template_name = "main/maintenanceobject_summary.html"

    def __init__(self):
        self.object = None
        super(TemplateView, self).__init__()

    def get_context_data(self, **kwargs):
        context = super(TemplateView, self).get_context_data(**kwargs)

        try:
            maintenance_object = MaintenanceObject.objects.get(pk=self.kwargs['object_id'])
        except ObjectDoesNotExist:
            raise Http404("Object does not exist")

        self.object = maintenance_object

        context['object'] = self.object
        context['nested_objects'] = MaintenanceObject.objects.filter(parent_id=self.object.id)[:10]
        context['related_events'] = MaintenanceEvent.objects.events_for(self.object)[:10]
        context['now'] = datetime.now()
        context['pending_links'] = MaintenanceLink.objects.pending_links(5, parent_object=self.object, future_days=14)
        breadcrumbs = list(self.object.get_parents())
        breadcrumbs.append(self.object)
        context['breadcrumbs'] = breadcrumbs
        return context


@method_decorator(login_required, name='dispatch')
class MaintenanceObjectEventList(ListView):
    model = MaintenanceEvent
    template_name = "main/maintenanceevent_list.html"
    context_object_name = 'related_events'
    paginate_by = 50

    def __init__(self):
        self.object = None
        super(ListView, self).__init__()

    def get(self, request, *args, **kwargs):
        try:
            maintenance_object = MaintenanceObject.objects.get(pk=self.kwargs['object_id'])
        except ObjectDoesNotExist:
            raise Http404("Object does not exist")

        self.object = maintenance_object

        return super(ListView, self).get(request)

    def get_context_data(self, **kwargs):
        context = super(ListView, self).get_context_data(**kwargs)
        context['object'] = self.object
        breadcrumbs = list(self.object.get_parents())
        breadcrumbs.append(self.object)
        context['breadcrumbs'] = breadcrumbs
        return context

    def get_queryset(self):
        return MaintenanceEvent.objects.events_for(self.object)


@method_decorator(login_required, name='dispatch')
class MaintenanceObjectList(ListView):
    model = MaintenanceObject
    template_name = "main/maintenanceobject_list.html"
    context_object_name = 'nested_objects'

    def __init__(self):
        super(ListView, self).__init__()
        self.parent = None

    def get(self, request, *args, **kwargs):

        if 'parent_id' in self.kwargs:
            try:
                maintenance_object = MaintenanceObject.objects.get(pk=self.kwargs['parent_id'])
            except ObjectDoesNotExist:
                raise Http404("Object does not exist")

            self.parent = maintenance_object

        return super(ListView, self).get(request)

    def get_context_data(self, **kwargs):
        context = super(ListView, self).get_context_data(**kwargs)
        breadcrumbs = []
        if self.parent:
            context['object'] = self.parent
            breadcrumbs = list(self.parent.get_parents())
            breadcrumbs.append(self.parent)
        context['breadcrumbs'] = breadcrumbs
        return context

    def get_queryset(self):
        kwargs = {}
        if self.parent:
            kwargs['parent_id'] = self.parent.id
        else:
            kwargs['parent_id__isnull'] = True
        return MaintenanceObject.objects.filter(**kwargs)


@method_decorator(login_required, name='dispatch')
class Dashboard(ListView):
    model = MaintenanceLink
    template_name = "main/dashboard.html"
    context_object_name = 'pending_links'

    def get_context_data(self, **kwargs):
        context = super(ListView, self).get_context_data(**kwargs)
        context['now'] = datetime.now()
        return context

    def get_queryset(self):
        return MaintenanceLink.objects.pending_links(50, future_days=7)


@method_decorator(login_required, name='dispatch')
class MaintenanceEventDeleteView(DeleteView):
    model = MaintenanceEvent
    pk_url_kwarg = 'event_id'

    def get_success_url(self):
        return reverse('main.object-summary', kwargs={'object_id': self.object.maintenance_object_id})


@method_decorator(login_required, name='dispatch')
class MaintenanceEventForm(FormView):
    form_class = EventForm
    template_name = "main/maintenanceevent_form.html"

    def __init__(self):
        self.event = None
        self.object = None
        super(FormView, self).__init__()

    def dispatch(self, request, *args, **kwargs):
        if 'object_id' in self.kwargs:
            try:
                self.object = MaintenanceObject.objects.get(pk=self.kwargs['object_id'])
            except ObjectDoesNotExist:
                raise Http404("Object not found")

        if 'event_id' in self.kwargs:
            try:
                self.event = MaintenanceEvent.objects.get(pk=self.kwargs['event_id'])
                self.object = self.event.maintenance_object
            except ObjectDoesNotExist:
                raise Http404("Object does not exist")

        return super(FormView, self).dispatch(request, *args, **kwargs)

    def get_form(self, form_class=None):
        if form_class is None:
            form_class = self.get_form_class()

        if self.event:
            kwargs = self.get_form_kwargs()
            kwargs['instance'] = self.event
            form = form_class(**kwargs)
        else:
            form = form_class(**self.get_form_kwargs())

        form.fields['maintenance_type'].queryset = MaintenanceType.objects \
            .filter(links__maintenance_object=self.object.id)
        form.fields['maintenance_date'].attributes = {'data-provide': 'datepicker'}
        return form

    def form_valid(self, form):
        if not self.event:
            new_event = form.save(commit=False)
            new_event.maintenance_object_id = self.object.id
            new_event.save()
        else:
            form.save()
        return redirect('main.object-summary', object_id=self.object.id)

from django.conf.urls import url

from main.views import MaintenanceObjectEventList, MaintenanceEventForm, MaintenanceEventDeleteView, \
    MaintenanceObjectList, Dashboard, MainView, MaintenanceObjectSummary


urlpatterns = [
    url(r'^$', MainView.as_view(), name='main.main'),
    url(r'^dashboard/$', Dashboard.as_view(), name='main.dashboard'),
    url(r'^objects/(?P<object_id>\d+)/$', MaintenanceObjectSummary.as_view(), name='main.object-summary'),
    url(r'^objects/(?P<parent_id>\d+)/nested/$', MaintenanceObjectList.as_view(), name='main.nested-objects-list'),
    url(r'^objects/$', MaintenanceObjectList.as_view(), name='main.top-objects-list'),
    url(r'^objects/(?P<object_id>\d+)/events/$', MaintenanceObjectEventList.as_view(), name='main.events-list'),
    url(r'^events/(?P<event_id>\d+)/edit/$', MaintenanceEventForm.as_view(), name='main.events-edit'),
    url(r'^objects/(?P<object_id>\d+)/add/$', MaintenanceEventForm.as_view(), name='main.events-add'),
    url(r'^events/(?P<event_id>\d+)/delete/$', MaintenanceEventDeleteView.as_view(), name='main.events-delete')
]

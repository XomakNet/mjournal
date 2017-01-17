from django.forms import ModelForm

from main.models import MaintenanceEvent


class EventForm(ModelForm):
    class Meta:
        model = MaintenanceEvent
        fields = ['maintenance_type', 'maintenance_date', 'comment']

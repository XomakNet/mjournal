from django.forms import ModelForm, TextInput

from main.models import MaintenanceEvent


class EventForm(ModelForm):
    class Meta:
        model = MaintenanceEvent
        fields = ['maintenance_type', 'maintenance_date', 'comment']
        widgets = {
            'maintenance_date': TextInput(attrs={'id': 'maintenance_date_picker'}),
        }

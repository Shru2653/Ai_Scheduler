from django import forms
from .models import Process

class ProcessForm(forms.ModelForm):
    class Meta:
        model = Process
        fields = ['name', 'arrival_time', 'burst_time', 'priority']
from django.core.management.base import BaseCommand
from properties.models import Property
import requests

class Command(BaseCommand):
    help = 'Rewrites property titles using the Ollama Phi model'

    def handle(self, *args, **kwargs):
        properties = Property.objects.all()
        
        for property in properties:
            original_title = property.title
            new_title = self.get_rewritten_title(original_title)
            
            if new_title:
                property.title = new_title
                property.save()
                self.stdout.write(self.style.SUCCESS(f'Successfully updated title for property ID {property.id}'))
            else:
                self.stdout.write(self.style.ERROR(f'Failed to update title for property ID {property.id}'))

    def get_rewritten_title(self, original_title):
        prompt = f"Rewrite the following property title in a more appealing way: {original_title}"
        url = "http://ollama:11434/v1/ollama/phi"
        headers = {"Content-Type": "application/json"}
        data = {"inputs": prompt}

        try:
            response = requests.post(url, json=data, headers=headers)
            response.raise_for_status()
            result = response.json()
            return result.get("text", "").strip()
        except requests.exceptions.RequestException as e:
            self.stdout.write(self.style.ERROR(f"Error calling Ollama API: {e}"))
            return None

import requests
import json
from django.db import connections
from django.core.management.base import BaseCommand
from properties.models import Property  # Replace with your actual model import

class Command(BaseCommand):
    help = 'Rewrite hotel title using an external service and generate a description'

    def handle(self, *args, **kwargs):
        # Set up connection to 'scraper_db' database (which is Postgres DB for hotels)
        with connections['trip'].cursor() as cursor:
            # Selecting only the columns city_id, city_name, hotel_id, hotelName, positionName, price, roomType, latitude, longitude
            cursor.execute('SELECT hotel_id, "hotelName", city_id, city_name, "positionName", price, "roomType", latitude, longitude FROM hotels')
            properties = cursor.fetchall()
            # Limit to only 3 hotels
            properties = properties[:2]  # Adjust as needed
        
        # Loop through hotels and use external API to rewrite titles and generate descriptions
        for hotel_id, hotelName, city_id, city_name, positionName, price, roomType, latitude, longitude in properties:
            try:
                # Rewrite the title with Ollama
                rewritten_title = self.rewrite_title_with_ollama(hotelName, city_name, positionName, price, roomType, latitude, longitude)
                
                # Generate a unique description
                description = self.generate_description(city_name, hotelName, positionName, roomType, price, latitude, longitude)

                # Save to ollama database
                Property.objects.create(
                    original_id=hotel_id,
                    original_title=hotelName,
                    rewritten_title=rewritten_title,
                    description=description
                )

                self.stdout.write(self.style.SUCCESS(
                    f"Original: {hotelName}\nRewritten: {rewritten_title}\nDescription: {description}\n"
                ))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error processing ID {hotel_id}: {str(e)}"))

    def generate_description(self, city_name, hotelName, positionName, roomType, price, latitude, longitude):
        # Generate a unique description based on provided hotel details
        prompt = (
            f"Create an engaging and unique hotel description based on the following details: "
            f"City: {city_name}, Hotel Name: {hotelName}, Position: {positionName}, Room Type: {roomType}, "
            f"Price: {price} USD per night, Latitude: {latitude}, Longitude: {longitude}. "
            f"Make sure to include the hotel's key features, its prime location, and provide a sense of what it would be like "
            f"for guests to stay there. The description should feel warm, inviting, and appealing to potential guests, "
            f"focusing on the experience of staying at this hotel. It should also reflect the vibe of the city and the local attractions."
        )
        
        # Make a request to the Ollama API to generate the description
        response = requests.post(
            "http://ollama:11434/api/generate",
            json={
                "model": "phi",  # You can try using other models if available
                "prompt": prompt,
                "system": "You are an expert hotel description writer. Your task is to generate a compelling and engaging hotel description based on the provided hotel details."
            }
        )

        if response.status_code == 200:
            try:
                response_data = json.loads(response.text)
                description = response_data.get('response', '').strip()

                # If the description is empty, use a fallback default
                if not description:
                    description = (
                        f"Experience a memorable stay at {hotelName} in {city_name}, located near {positionName}. "
                        f"With {roomType} rooms available for only {price} USD per night, this hotel offers the perfect balance of "
                        f"comfort and convenience. Whether you're here for business or leisure, {hotelName} is the ideal base to explore "
                        f"the best of {city_name}. Book your stay and make the most of your visit!"
                    )
                return description
            except json.JSONDecodeError:
                return "Description not available"
        else:
            return f"Error generating description: {response.text}"

    def rewrite_title_with_ollama(self, title, city_name, positionName, price, roomType, latitude, longitude):
        prompt = (
            f"You are a hotel branding expert. Your task is to create a catchy, unique, and SEO-friendly hotel title that "
            f"captures the essence of the location and the hotel experience. The new title should reflect the city's vibe, "
            f"mention nearby attractions, and incorporate features like room type and price, while being distinct from the original name. "
            f"Original hotel name: '{title}', City: '{city_name}', Nearby location: '{positionName}', Room Type: '{roomType}', "
            f"Price: {price} USD per night, Latitude: {latitude}, Longitude: {longitude}. "
            f"Your title should make the hotel stand out while maintaining a connection to the city and the guest experience."
        )

        response = requests.post(
            "http://ollama:11434/api/generate",
            json={
                "model": "phi",  # You can try using different models if available
                "prompt": prompt,
                "system": "You are an expert in creative hotel branding. Respond only with a creative, unique, and SEO-optimized hotel title."
            }
        )

        if response.status_code == 200:
            try:
                response_data = json.loads(response.text)
                rewritten_title = response_data.get('response', '').strip()

                # If the rewritten title is the same as the original, add a fallback
                if rewritten_title.lower() == title.lower():
                    rewritten_title += " - A Premium Experience in " + city_name

                return rewritten_title
            except json.JSONDecodeError:
                return title
        else:
            self.stdout.write(self.style.WARNING(f"Error from Ollama: {response.text}"))
            return title

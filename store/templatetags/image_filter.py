from django import template
from PIL import Image

register = template.Library()

@register.filter
def resize_image(image_url, height):
    # Open the image using Pillow
    image = Image.open(image_url)

    # Calculate the new width proportional to the desired height
    width = int(height * image.width / image.height)

    # Resize the image
    resized_image = image.resize((width, height))

    # Save the resized image to a temporary file
    resized_image_path = 'media/resized/'  # Replace with your desired path
    resized_image.save(resized_image_path)

    # Return the URL of the resized image
    return resized_image_path

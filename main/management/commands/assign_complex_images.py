import os
import random
from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.files import File
from main.models import ResidentialComplex

class Command(BaseCommand):
    help = 'Assigns random images from media/complexes to ResidentialComplex objects.'

    def handle(self, *args, **options):
        media_complexes_dir = os.path.join(settings.MEDIA_ROOT, 'complexes')
        
        if not os.path.exists(media_complexes_dir):
            self.stdout.write(self.style.ERROR(f"Directory '{media_complexes_dir}' does not exist. Please ensure you have images in media/complexes/"))
            return

        image_files = [f for f in os.listdir(media_complexes_dir) if os.path.isfile(os.path.join(media_complexes_dir, f))]
        
        if not image_files:
            self.stdout.write(self.style.WARNING(f"No image files found in '{media_complexes_dir}'."))
            return

        complexes = ResidentialComplex.objects.all()
        
        if not complexes.exists():
            self.stdout.write(self.style.WARNING("No ResidentialComplex objects found in the database."))
            return

        self.stdout.write(self.style.SUCCESS(f"Found {len(image_files)} images in media/complexes/"))
        self.stdout.write(self.style.SUCCESS(f"Assigning images to {complexes.count()} ResidentialComplex objects..."))

        for complex_obj in complexes:
            random_image_name = random.choice(image_files)
            image_path = os.path.join(media_complexes_dir, random_image_name)

            try:
                with open(image_path, 'rb') as f:
                    # Clear existing image if any, to avoid multiple files for one object
                    if complex_obj.image:
                        complex_obj.image.delete(save=False) # Delete old file, but don't save yet

                    complex_obj.image.save(random_image_name, File(f), save=True)
                    self.stdout.write(self.style.SUCCESS(f"Successfully assigned '{random_image_name}' to '{complex_obj.name}'"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error assigning image to '{complex_obj.name}': {e}"))

        self.stdout.write(self.style.SUCCESS("Image assignment complete!")) 
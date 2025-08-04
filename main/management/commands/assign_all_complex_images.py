import os
import random
from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.files import File
from main.models import ResidentialComplex

class Command(BaseCommand):
    help = 'Assigns multiple random images from media/complexes to ResidentialComplex objects (main + additional images).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--main-only',
            action='store_true',
            help='Assign only main image (image field)',
        )
        parser.add_argument(
            '--additional-only',
            action='store_true',
            help='Assign only additional images (image_2, image_3, image_4)',
        )

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
            self.stdout.write(f"\nProcessing: {complex_obj.name}")
            
            # Assign main image
            if not options['additional_only']:
                self.assign_image_to_field(complex_obj, 'image', image_files, "Main image")
            
            # Assign additional images
            if not options['main_only']:
                for i in range(2, 5):  # image_2, image_3, image_4
                    field_name = f'image_{i}'
                    self.assign_image_to_field(complex_obj, field_name, image_files, f"Additional image {i}")

        self.stdout.write(self.style.SUCCESS("\nImage assignment complete!"))

    def assign_image_to_field(self, complex_obj, field_name, image_files, description):
        """Assign a random image to a specific field"""
        try:
            # Get current field value
            current_image = getattr(complex_obj, field_name)
            
            # Clear existing image if any
            if current_image:
                current_image.delete(save=False)
            
            # Select random image
            random_image_name = random.choice(image_files)
            image_path = os.path.join(settings.MEDIA_ROOT, 'complexes', random_image_name)
            
            # Assign new image
            with open(image_path, 'rb') as f:
                getattr(complex_obj, field_name).save(random_image_name, File(f), save=False)
            
            self.stdout.write(self.style.SUCCESS(f"  ✓ {description}: '{random_image_name}'"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  ✗ Error assigning {description}: {e}"))
        
        # Save the object after all field assignments
        complex_obj.save() 
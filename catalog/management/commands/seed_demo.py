from django.core.management.base import BaseCommand

from catalog.demo import seed_demo


class Command(BaseCommand):
    help = "Create or update the demo products and shipping boxes."

    def handle(self, *args, **options):
        products, boxes = seed_demo()
        self.stdout.write(self.style.SUCCESS(f"Seeded {products} products and {boxes} boxes."))

# Fichier généré automatiquement pour structure propre.
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from apps.core.models import Module, Page

MODULE_STRUCTURE = [
    {
        "name": "Administration",
        "order": 1,
        "display_mod": "card-view",
        "icon": "settings-icon",
        "pages": [
            {
                "title": "Comptes Utilisateurs",
                "icon": "user-icon",
                "order": 0,
                "link": "/users",
                "tags": ["user"]
            },
            {
                "title": "Rôles & Permissions",
                "icon": "role-icon",
                "order": 1,
                "link": "/roles",
                "tags": ["role"]
            }
        ]
    }
]

class Command(BaseCommand):
    help = "Crée les Modules et les Pages pour la navigation."

    def handle(self, *args, **options):
        self.stdout.write("--- Debut du seeding Navigation ---")
        Page.all_objects.all().hard_delete()
        Module.all_objects.all().hard_delete()
        
        for mod_item in MODULE_STRUCTURE:
            if not isinstance(mod_item, dict):
                continue
            mod_data = dict(mod_item)
            pages_data = mod_data.pop('pages', [])
            mod_code = f"mod-{slugify(str(mod_data.get('name', '')))}"
            icon_name = mod_data.get('icon', '')
            if icon_name:
                mod_data['icon'] = f"/apps/core/assets/icons/{icon_name}.svg"
            
            module = Module.objects.create(code=mod_code, **mod_data)
            for page_data in pages_data:
                page_icon_name = page_data.get('icon', '')
                page_icon_url = f"/apps/core/assets/icons/{page_icon_name}.svg" if page_icon_name else ""
                Page.objects.create(
                    module=module,
                    title=page_data.get('title', ''),
                    icon=page_icon_url,
                    order=page_data.get('order', 1),
                    link=page_data.get('link', ''),
                    permission_tags=page_data.get('tags', [])
                )
        self.stdout.write("--- Seeding Navigation termine ---")

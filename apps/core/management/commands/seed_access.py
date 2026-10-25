# Fichier généré automatiquement pour structure propre.
from django.core.management.base import BaseCommand
from apps.core.models import Group, Permission
from typing import List, Dict, Any

GROUP_STRUCTURE: List[Dict[str, Any]] = [
    {
        "name": "Gestion des Utilisateurs",
        "tag": "user",
        "permissions": [
            {"name": "Lire les utilisateurs", "codename": "view_user"},
            {"name": "Ajouter un utilisateur", "codename": "add_user"},
            {"name": "Modifier un utilisateur", "codename": "change_user"},
            {"name": "Supprimer un utilisateur", "codename": "delete_user"},
        ]
    },
    {
        "name": "Gestion des Rôles",
        "tag": "role",
        "permissions": [
            {"name": "Lire les rôles", "codename": "view_role"},
            {"name": "Ajouter un rôle", "codename": "add_role"},
            {"name": "Modifier un rôle", "codename": "change_role"},
            {"name": "Supprimer un rôle", "codename": "delete_role"},
        ]
    },
    {
        "name": "Gestion des Etablissements",
        "tag": "establishment",
        "permissions": [
            {"name": "Lire les établissements", "codename": "view_establishment"},
            {"name": "Ajouter un établissement", "codename": "add_establishment"},
            {"name": "Modifier un établissement", "codename": "change_establishment"},
            {"name": "Supprimer un établissement", "codename": "delete_establishment"},
        ]
    },
]

class Command(BaseCommand):
    help = "Crée les Permissions et les Groupes selon la structure définie."

    def handle(self, *args, **options):
        self.stdout.write(getattr(self.style, 'NOTICE', lambda x: x)("--- Début du seeding Access (Permissions & Groups) ---"))
        for group_data in GROUP_STRUCTURE:
            group_name = group_data['name']
            tag = group_data['tag']
            group, created = Group.objects.get_or_create(name=group_name)
            if created:
                self.stdout.write(f"  Groupe '{group_name}' créé.")
            group.permissions.clear()
            for perm_data in group_data['permissions']:
                perm, p_created = Permission.objects.get_or_create(
                    codename=perm_data['codename'],
                    defaults={'name': perm_data['name'], 'tag': tag}
                )
                if p_created:
                    self.stdout.write(f"    Permission '{perm.codename}' créée.")
                else:
                    if perm.tag != tag or perm.name != perm_data['name']:
                        perm.tag = tag
                        perm.name = perm_data['name']
                        perm.save()
                group.permissions.add(perm)
            self.stdout.write(getattr(self.style, 'SUCCESS', lambda x: x)(f"  ✔ Permissions pour '{group_name}' synchronisées."))
        self.stdout.write(getattr(self.style, 'SUCCESS', lambda x: x)("--- Seeding Access terminé ---"))

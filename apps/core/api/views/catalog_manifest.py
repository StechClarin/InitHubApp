# apps/core/api/views/catalog_manifest.py
import os
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils.text import slugify

from apps.core.management.commands.seed_navigation import MODULE_STRUCTURE
from apps.core.management.commands.seed_access import GROUP_STRUCTURE

class CatalogManifestView(APIView):
    """
    ENDPOINT DE MANIFESTE CATALOGUE - STORE & INITHUB
    --------------------------------------------------
    Renvoie la liste dynamique de tous les modules de l'application,
    leurs pages avec tags associés, ainsi que les options transversales (free_tags).
    Calcul automatique : tout tag présent dans seed_access non rattaché à une page
    de seed_navigation est extrait comme Free Tag.
    """
    authentication_classes = []
    permission_classes = []

    def get(self, request, *args, **kwargs):
        # 1. Validation Clé de Transport Sécurisée Hub / Store
        api_key = request.headers.get('X-Hub-Api-Key')
        expected_key = os.environ.get('HUB_API_KEY', 'ethernanos-hub-secret-2026')

        if not api_key or api_key != expected_key:
            return Response(
                {"error": "Unauthorized: Invalid API Key"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # 2. Construction dynamique des modules et de leurs tags
        modules_manifest = []
        all_nav_tags = set()

        for mod in MODULE_STRUCTURE:
            if not isinstance(mod, dict):
                continue

            name = mod.get('name', '')
            code = f"mod-{slugify(str(name))}"
            icon = mod.get('icon', '')

            # Extraction des tags et des pages
            mod_tags = set()
            pages_list = []
            for p in mod.get('pages', []):
                if not isinstance(p, dict):
                    continue
                p_tags = p.get('tags', [])
                if isinstance(p_tags, list):
                    mod_tags.update(p_tags)
                    all_nav_tags.update(p_tags)
                pages_list.append({
                    "title": p.get('title', ''),
                    "link": p.get('link', ''),
                    "icon": p.get('icon', ''),
                    "tags": p_tags
                })

            modules_manifest.append({
                "code": code,
                "name": name,
                "icon": icon,
                "order": mod.get('order', 0),
                "tags": sorted(list(mod_tags)),
                "pages": pages_list
            })

        # 3. Extraction dynamique des Free Tags depuis seed_access (GROUP_STRUCTURE)
        free_tags_manifest = []
        seen_tags = set()

        for group in GROUP_STRUCTURE:
            if not isinstance(group, dict):
                continue
            tag = group.get('tag')
            if tag and tag not in all_nav_tags and tag not in seen_tags:
                seen_tags.add(tag)
                free_tags_manifest.append({
                    "tag": tag,
                    "label": group.get('name', tag),
                    "description": f"Capacité transversale système ({group.get('name', tag)})",
                    "permissions": [p.get('codename') for p in group.get('permissions', []) if isinstance(p, dict)]
                })

        app_name = os.environ.get('APP_NAME', 'InitHub Starter')
        app_code = os.environ.get('APP_CODE', 'inithub-starter')

        return Response({
            "app_name": app_name,
            "app_code": app_code,
            "modules": modules_manifest,
            "free_tags": free_tags_manifest
        }, status=status.HTTP_200_OK)

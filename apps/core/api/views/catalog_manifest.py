# apps/core/api/views/catalog_manifest.py
import os
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils.text import slugify

from apps.core.management.commands.seed_navigation import MODULE_STRUCTURE
from apps.core.constants.licensing import FREE_TAGS_CONFIG

class CatalogManifestView(APIView):
    """
    ENDPOINT DE MANIFESTE CATALOGUE - STORE & INITHUB
    --------------------------------------------------
    Renvoie la liste dynamique de tous les modules de l'application,
    leurs pages avec tags associés, ainsi que les options transversales (free_tags).
    Permet au Store (port_folio) et au Hub d'adapter leurs licences sans hardcoder les codes.
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

        app_name = os.environ.get('APP_NAME', 'InitHub Starter')
        app_code = os.environ.get('APP_CODE', 'inithub-starter')

        return Response({
            "app_name": app_name,
            "app_code": app_code,
            "modules": modules_manifest,
            "free_tags": FREE_TAGS_CONFIG
        }, status=status.HTTP_200_OK)

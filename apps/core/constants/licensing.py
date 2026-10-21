# apps/core/constants/licensing.py
"""
Configuration centralisée des options et tags transversaux (Free Tags) pour InitHubApp.
Ce fichier sert de contrat socle pour le catalogue du Store (port_folio) et le vérificateur de licences.
Chaque application métier dérivée peut enregistrer ses options payantes transversales ici.
"""

FREE_TAGS_CONFIG = [
    # Les applications dérivées (ex: School Manage, E-Commerce, etc.)
    # définissent ici leurs options transversales :
    # {
    #     "tag": "graphix",
    #     "name": "Option Graphix",
    #     "label": "Option Graphix",
    #     "description": "Visualisation de graphiques avancés",
    #     "module_code": "mod-example",
    # },
]

FREE_TAG_MODULE_MAP = {item["tag"]: item["module_code"] for item in FREE_TAGS_CONFIG}

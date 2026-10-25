# apps/core/models/tenant_license.py
from django.db import models
from django.conf import settings
from .user_audit_model import UserAuditModel

class TenantLicense(UserAuditModel):
    """
    Modèle de stockage des licences de modules déverrouillés par Propriétaire (Tenant / User).
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="licenses",
        verbose_name="Propriétaire (Owner)",
        null=True,
        blank=True
    )
    module_code = models.CharField(
        max_length=100,
        help_text="Code technique unique du module (ex: mod-finance)",
        verbose_name="Code du Module"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Définit si le module est débloqué par la licence",
        verbose_name="Est Actif"
    )
    allowed_pages = models.JSONField(
        default=list,
        blank=True,
        help_text="Liste des tags/pages autorisés pour ce module (conservé pour rétrocompatibilité).",
        verbose_name="Pages Autorisées (Legacy)"
    )
    allowed_tags = models.JSONField(
        default=list,
        blank=True,
        help_text="Liste unifiée des tags autorisés pour ce module (pages ou options transversales).",
        verbose_name="Tags Autorisés"
    )
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Date d'expiration de la licence (null = illimitée)",
        verbose_name="Date d'Expiration"
    )

    def get_effective_tags(self):
        """
        Règle d'or du repli 'OR' :
        Si allowed_tags contient des éléments, on l'utilise en priorité.
        Sinon, on se rabat sur l'ancien allowed_pages pour rétrocompatibilité.
        """
        if self.allowed_tags:
            return self.allowed_tags
        return self.allowed_pages or []

    class Meta:
        unique_together = ['user', 'module_code']
        verbose_name = "Licence Tenant"
        verbose_name_plural = "Licences Tenants"

    def __str__(self):
        username = getattr(self.user, 'username', 'N/A') if self.user else "N/A"
        hub_id = getattr(self.user, 'hub_id', 'N/A') if self.user else "N/A"
        return f"{username} (Hub: {hub_id}) -> {self.module_code} ({'Actif' if self.is_active else 'Inactif'})"

    @classmethod
    def verify_access(cls, request, establishment_id, codename):
        """
        Vérifie si la licence de l'établissement autorise l'accès pour un codename de permission donné.
        Utilise un cache au niveau du cycle de vie de la requête pour optimiser les performances.
        """
        if not establishment_id:
            return True

        if not hasattr(request, '_license_access_cache'):
            request._license_access_cache = {}

        cache_key = f"{establishment_id}:{codename}"
        if cache_key in request._license_access_cache:
            return request._license_access_cache[cache_key]

        from apps.core.models import Permission, Page, Establishment
        
        # 1. Récupération de la permission et de son tag
        perm = Permission.objects.filter(codename=codename).first()
        if not perm or not perm.tag:
            request._license_access_cache[cache_key] = True
            return True

        # 2. Récupération de la page et du module liés à ce tag
        # IMPORTANT : le lookup JSON `__contains` n'est PAS supporté sur SQLite (mode Hub local).
        # On filtre en Python pour rester 100% agnostique PostgreSQL & SQLite.
        page = next(
            (
                p
                for p in Page.objects.select_related("module")
                if perm.tag in (p.permission_tags or [])
            ),
            None,
        )

        is_free_tag = False
        if page:
            module_code = page.module.code
            core_codes = ['mod-referentiel', 'mod-administration']
            if module_code in core_codes:
                request._license_access_cache[cache_key] = True
                return True
        else:
            from apps.core.constants.licensing import FREE_TAG_MODULE_MAP
            module_code = FREE_TAG_MODULE_MAP.get(perm.tag, "mod-free")
            is_free_tag = True

        # 3. Vérification de la licence pour ce module
        from django.core.exceptions import ObjectDoesNotExist
        try:
            est = Establishment.objects.get(id=establishment_id)
        except ObjectDoesNotExist:
            request._license_access_cache[cache_key] = False
            return False

        if is_free_tag:
            # Support hybride : conteneur générique 'mod-free', module parent, tag brut ou préfixé
            licence = cls.objects.filter(
                user=est.user,
                module_code__in=["mod-free", module_code, perm.tag, f"free-{perm.tag}"],
                is_active=True
            ).first()
        else:
            licence = cls.objects.filter(
                user=est.user,
                module_code=module_code,
                is_active=True
            ).first()

        if not licence:
            request._license_access_cache[cache_key] = False
            return False

        # 3.5. Vérification d'expiration de la licence
        from django.utils import timezone
        if licence.expires_at and licence.expires_at < timezone.now():
            request._license_access_cache[cache_key] = False
            return False

        # 4. Si la licence a des restrictions (tags spécifiés), ou s'il s'agit d'un tag libre optionnel
        effective_tags = licence.get_effective_tags()
        if is_free_tag:
            # Un tag libre optionnel doit impérativement figurer dans les tags autorisés
            if perm.tag not in effective_tags:
                request._license_access_cache[cache_key] = False
                return False
        elif effective_tags:
            # Pour une page standard, si des restrictions sont définies, le tag doit y figurer
            if perm.tag not in effective_tags:
                request._license_access_cache[cache_key] = False
                return False

        request._license_access_cache[cache_key] = True
        return True

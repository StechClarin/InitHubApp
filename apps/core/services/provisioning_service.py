from django.db.transaction import atomic
from django.conf import settings
from django.core.mail import send_mail
from apps.core.models import Establishment
from apps.profilmanagement.models import User, Role
import logging

logger = logging.getLogger(__name__)

class ProvisioningService:
    """
    Service centralisé pour le provisioning industriel des Tenants (Etablissements).
    Gère la création atomique de l'utilisateur, de l'établissement et les notifications.
    """

    @staticmethod
    def provision_tenant(tenant_id, tenant_name, hub_id=None, admin_email=None, password='admin1234', send_welcome_email=True, included_mods=None):
        """
        Orchestre le provisioning complet d'un nouveau site.
        """
        target_email = admin_email if admin_email else 'ethernanos@gmail.com'
        results = {
            "status": "pending",
            "user_created": False,
            "establishment_created": False,
            "error": None
        }

        try:
            # pyrefly: ignore [bad-context-manager]
            with atomic():
                # 1. Création/Récupération de l'Administrateur
                user, results["user_created"] = User.objects.get_or_create(
                    email=target_email,
                    defaults={
                        'username': target_email,
                        'is_active': True,
                        'is_staff': True,
                        'is_superuser': False
                    }
                )

                if results["user_created"]:
                    user.set_password(password)
                    user.save()
                    logger.info(f"Nouveau compte admin créé pour {target_email}")

                # 2. Création/Mise à jour de l'Établissement (Site)
                establishment, results["establishment_created"] = Establishment.objects.get_or_create(
                    code=tenant_id,
                    defaults={
                        'name': tenant_name,
                        'user': user
                    }
                )

                if not results["establishment_created"]:
                    establishment.name = tenant_name
                    establishment.user = user
                    establishment.save()
                    logger.info(f"Mise à jour de l'établissement existant : {tenant_id}")

                # 4. Liaison Hub / Tenant (Règle Métier : hub_id = owner)
                if hub_id:
                    user.hub_id = hub_id
                else:
                    user.hub_id = tenant_id
                user.save()

                # 5. Création du Membership (Contextual Access)
                from apps.core.services.establishment_membership_service import EstablishmentMembershipService
                membership_service = EstablishmentMembershipService()
                
                # On récupère le rôle admin pour le membership
                admin_role, _ = Role.objects.get_or_create(name='admin')
                
                membership_service.create_or_update_with_roles(
                    user=user,
                    establishment=establishment,
                    roles=[admin_role],
                    is_owner=True, # Provisioning d'un tenant = Ownership
                    status='active'
                )

                # 4.5. Enregistrement des Licences Incluses
                if included_mods:
                    from apps.core.models import TenantLicense
                    for code in included_mods:
                        if code:
                            TenantLicense.objects.update_or_create(
                                user=user,
                                module_code=code,
                                defaults={
                                    'is_active': True,
                                    'allowed_tags': [],
                                    'allowed_pages': []
                                }
                            )

                # 5. Envoi de l'email de bienvenue (si activé et nouvel utilisateur)
                if send_welcome_email and results["user_created"]:
                    ProvisioningService._send_welcome_email(target_email, tenant_name, password)

                results["status"] = "success"
                results["user_email"] = user.email
                results["establishment_code"] = establishment.code
                results["establishment_name"] = establishment.name

                return results

        except Exception as e:
            logger.error(f"Echec du provisioning pour {tenant_id}: {str(e)}")
            results["status"] = "failed"
            results["error"] = str(e)
            raise e

    @staticmethod
    def _send_welcome_email(email, tenant_name, password):
        """Helper interne pour l'envoi d'email"""
        try:
            subject = f"Vos accès Administrateur pour {tenant_name}"
            message = (
                f"Bonjour,\n\n"
                f"Votre application School Manage a été déverrouillée.\n"
                f"Voici vos identifiants d'accès (rôle admin) :\n\n"
                f"Email : {email}\n"
                f"Mot de passe : {password}\n\n"
                f"Merci d'utiliser EtherNanos."
            )
            from_email = settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@ethernanos.com'
            
            send_mail(
                subject=subject,
                message=message,
                from_email=from_email,
                recipient_list=[email],
                fail_silently=True,
            )
            logger.info(f"Email de bienvenue envoyé à {email}")
        except Exception as e:
            logger.warning(f"Impossible d'envoyer l'email à {email}: {str(e)}")

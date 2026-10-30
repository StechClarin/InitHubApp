from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()

class EmailOrUsernameModelBackend(ModelBackend):
    """
    Authentification via Username OU Email + DOUBLE LOCK HUB.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        # Récupération du Tenant verrouillé par le Hub
        hub_tenant_id = request.session.get('hub_tenant_id') if request else None
        
        if not username:
            return None

        clean_identifier = str(username).strip()
        # On cherche un user qui matche username OU email de manière insensible à la casse (iexact)
        user = User.objects.filter(
            Q(username__iexact=clean_identifier) | Q(email__iexact=clean_identifier)
        ).first()

        if not user:
            return None

        # --- VERIFICATION DU DOUBLE LOCK ---
        if hub_tenant_id:
            # 1. Vérifier si c'est le Propriétaire (Tenant)
            is_owner = user.establishments_owned.filter(code=hub_tenant_id).exists()
            
            # 2. Vérifier si c'est un Personnel de ce Tenant
            # (L'établissement doit appartenir au code du Hub)
            is_staff = user.employments.filter(establishment__code=hub_tenant_id).exists()
            
            if not is_owner and not is_staff:
                # L'utilisateur existe, mais il n'appartient pas au bâtiment ouvert par le Hub
                return None
        # -----------------------------------

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None

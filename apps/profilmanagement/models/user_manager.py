# apps/profilmanagement/models/user_manager.py
from django.contrib.auth.models import BaseUserManager
from apps.core.models.user_audit_model import SoftDeleteQuerySet

class UserManager(BaseUserManager):
    """
    Manager personnalisé pour notre modèle User.
    Intègre la logique de suppression logique (Soft Delete).
    """
    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db).filter(is_deleted=False)

    def get_by_natural_key(self, username):
        """
        Permet l'authentification insensible à la casse sur USERNAME_FIELD
        """
        return self.get(**{f"{self.model.USERNAME_FIELD}__iexact": str(username).strip()})

    def create_user(self, username, email, password=None, **extra_fields):
        """
        Crée et sauvegarde un utilisateur avec un email et un mot de passe normalisés.
        """
        if not username:
            raise ValueError("Le nom d'utilisateur est obligatoire")
        if not email:
            raise ValueError("L'email est obligatoire")
        
        username = str(username).strip().lower()
        email = self.normalize_email(email).strip().lower()
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        """
        Crée et sauvegarde un super-utilisateur.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Le super-utilisateur doit avoir is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Le super-utilisateur doit avoir is_superuser=True.')

        return self.create_user(username, email, password, **extra_fields)
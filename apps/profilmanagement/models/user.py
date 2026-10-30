# apps/profilmanagement/models/user.py
import uuid
from typing import Any
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from .role import Role
from apps.documents.utils import document_upload_path
from .user_manager import UserManager

from apps.core.models.user_audit_model import UserAuditModel

class User(UserAuditModel, AbstractBaseUser, PermissionsMixin):
    # ... (Champs standards inchangés : username, email, etc.) ...
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    is_staff = models.BooleanField(default=False)
    is_active: Any = models.BooleanField(default=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    phone = models.CharField(max_length=50, blank=True, null=True, verbose_name="Téléphone")
    hub_id = models.CharField(max_length=100, blank=True, null=True, verbose_name="Hub ID", db_index=True)

    photo = models.ImageField(upload_to=document_upload_path, blank=True, null=True)

    # roles = models.ManyToManyField(Role, ...) -> Déplacé vers EstablishmentMembership
    # establishment = models.ForeignKey(...)   -> Déplacé vers EstablishmentMembership

    objects = UserManager()

    EMAIL_FIELD = 'email'
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    class Meta:
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"

    def clean(self):
        super().clean()
        if self.email:
            self.email = self.email.strip().lower()
        if self.username:
            self.username = self.username.strip().lower()

    def save(self, *args, **kwargs):
        if self.email:
            self.email = self.email.strip().lower()
        if self.username:
            self.username = self.username.strip().lower()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return str(self.username)

    groups: Any = None
    user_permissions: Any = None
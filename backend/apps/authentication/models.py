"""
Authentication & Security models.
TZ §6.1, §5 — RBAC/ABAC, JWT, 2FA (TOTP), audit_logs.
Tables: users, roles, user_roles, permissions, role_permissions,
        sessions, tokens, 2fa_data, audit_logs
"""
import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin


# ───────────────────────────── Enums ──────────────────────────────

class UserRole(models.TextChoices):
    """8 ролей согласно ТЗ §5."""
    SUPER_ADMIN     = 'SUPER_ADMIN',     'Суперадминистратор'
    ADMIN           = 'ADMIN',           'Администратор'
    DEPARTMENT_HEAD = 'DEPARTMENT_HEAD', 'Руководитель отдела'
    PROJECT_MANAGER = 'PROJECT_MANAGER', 'Руководитель проекта'
    TEAM_LEAD       = 'TEAM_LEAD',       'Тимлид'
    EMPLOYEE        = 'EMPLOYEE',        'Сотрудник'
    ANALYST         = 'ANALYST',         'Аналитик'
    GUEST           = 'GUEST',           'Гость'


# ────────────────────────── User Manager ──────────────────────────

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)   # bcrypt/Argon2 via Django
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('role', UserRole.SUPER_ADMIN)
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)


# ────────────────────────────── User ──────────────────────────────

class User(AbstractBaseUser, PermissionsMixin):
    """
    TZ §6.1 — авторизация, 2FA, блокировка после 5 попыток,
    JWT HttpOnly cookies, смена пароля через email.
    Соответствует таблице `users` + поля из `2fa_data`.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Аутентификация
    email          = models.EmailField(unique=True)
    tab_number     = models.CharField(max_length=30, unique=True, null=True, blank=True,
                                      help_text='Табельный номер (альтернативный логин)')
    role           = models.CharField(max_length=30, choices=UserRole.choices, default=UserRole.EMPLOYEE)

    # Профиль
    first_name     = models.CharField(max_length=100)
    last_name      = models.CharField(max_length=100)
    middle_name    = models.CharField(max_length=100, blank=True)

    # 2FA (TOTP — Google Authenticator, YubiKey)
    is_2fa_enabled = models.BooleanField(default=False)
    totp_secret    = models.CharField(max_length=64, blank=True, null=True)

    # Безопасность — блокировка после 5 неудачных попыток
    failed_login_attempts = models.IntegerField(default=0)
    is_locked             = models.BooleanField(default=False)
    locked_until          = models.DateTimeField(null=True, blank=True)

    # Стандартные флаги Django
    is_active  = models.BooleanField(default=True)
    is_staff   = models.BooleanField(default=False)

    # Audit
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)
    last_login_at = models.DateTimeField(null=True, blank=True)

    # Soft-delete
    is_deleted  = models.BooleanField(default=False)
    deleted_at  = models.DateTimeField(null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD  = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        db_table = 'users'
        verbose_name = 'Пользователь'
        verbose_name_plural = "Пользователи"
        indexes = [
            models.Index(fields=['email'], name='users_email_idx'),
            models.Index(fields=['tab_number'], name='users_tab_idx'),
        ]

    def __str__(self):
        return f'{self.last_name} {self.first_name} <{self.email}>'

    @property
    def full_name(self):
        return f'{self.last_name} {self.first_name} {self.middle_name}'.strip()


# ──────────────────────────── Session ─────────────────────────────

class Session(models.Model):
    """
    TZ §6.1 — хранение активных сессий в Redis/PostgreSQL
    с возможностью принудительного завершения.
    Соответствует таблицам `sessions` + `tokens`.
    """
    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user         = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    refresh_token_hash = models.CharField(max_length=256)  # hashed
    user_agent   = models.TextField(blank=True)
    ip_address   = models.GenericIPAddressField(null=True, blank=True)
    created_at   = models.DateTimeField(auto_now_add=True)
    expires_at   = models.DateTimeField()
    is_active    = models.BooleanField(default=True)

    class Meta:
        db_table = 'sessions'
        indexes = [
            models.Index(fields=['user', 'is_active'], name='sessions_user_active_idx'),
        ]


# ────────────────────────── Permission ────────────────────────────

class Permission(models.Model):
    """Таблица `permissions` — атомарные права доступа для ABAC."""
    codename    = models.CharField(max_length=100, unique=True)
    description = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = 'permissions'


class RolePermission(models.Model):
    """Таблица `role_permissions` — связь роль→право."""
    role       = models.CharField(max_length=30, choices=UserRole.choices)
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE)

    class Meta:
        db_table = 'role_permissions'
        unique_together = ('role', 'permission')


# ─────────────────────────── AuditLog ─────────────────────────────

class AuditLog(models.Model):
    """
    TZ §11 — полное журналирование действий пользователей.
    Таблица `audit_logs`.
    """
    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user       = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='audit_logs')
    action     = models.CharField(max_length=200)
    entity     = models.CharField(max_length=100, blank=True)   # e.g. 'Employee', 'Absence'
    entity_id  = models.UUIDField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    details    = models.JSONField(default=dict)
    timestamp  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'audit_logs'
        indexes = [
            models.Index(fields=['user', 'timestamp'], name='audit_user_ts_idx'),
            models.Index(fields=['entity', 'entity_id'], name='audit_entity_idx'),
        ]

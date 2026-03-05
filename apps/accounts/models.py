from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.conf import settings


class UserProfile(models.Model):
    """Profil utilisateur étendu."""
    LANGUAGE_CHOICES = [
        ('fr', 'Français'),
        ('nl', 'Nederlands'),
        ('ru', 'Русский'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    language = models.CharField('Langue', max_length=5, choices=LANGUAGE_CHOICES, default='fr')
    avatar = models.ImageField('Avatar', upload_to='avatars/', blank=True, null=True)
    bio = models.TextField('Bio', blank=True)

    # Premium
    is_premium = models.BooleanField('Premium', default=False)
    premium_until = models.DateTimeField('Premium jusqu\'à', blank=True, null=True)

    # Statistics
    total_questions_answered = models.IntegerField('Questions répondues', default=0)
    correct_answers = models.IntegerField('Réponses correctes', default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Profil utilisateur'
        verbose_name_plural = 'Profils utilisateurs'

    def __str__(self):
        return f'{self.user.username}'

    @property
    def has_active_premium(self):
        """Vérifie si l'abonnement premium est actif."""
        if not self.is_premium:
            return False
        if self.premium_until and self.premium_until < timezone.now():
            self.is_premium = False
            self.save(update_fields=['is_premium'])
            return False
        return True

    @property
    def success_rate(self):
        """Taux de réussite en pourcentage."""
        if self.total_questions_answered == 0:
            return 0
        return round(self.correct_answers / self.total_questions_answered * 100, 1)

    def increment_stats(self, is_correct):
        """Met à jour les statistiques après une réponse."""
        self.total_questions_answered += 1
        if is_correct:
            self.correct_answers += 1
        self.save(update_fields=['total_questions_answered', 'correct_answers'])

    def save(self, *args, **kwargs):
        _original = self.__class__.objects.filter(pk=self.pk).values_list('avatar', flat=True).first() if self.pk else None
        super().save(*args, **kwargs)
        if self.avatar and self.avatar.name and self.avatar.name != _original:
            from apps.main.image_utils import convert_field_to_webp
            if convert_field_to_webp(self.avatar):
                self.__class__.objects.filter(pk=self.pk).update(avatar=self.avatar.name)


class DailyQuota(models.Model):
    """Quota quotidien de questions pour les utilisateurs gratuits."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='daily_quotas')
    date = models.DateField('Date', default=timezone.now)
    questions_answered = models.IntegerField('Questions répondues', default=0)
    max_questions = models.IntegerField(
        'Maximum questions',
        default=15
    )

    class Meta:
        verbose_name = 'Quota quotidien'
        verbose_name_plural = 'Quotas quotidiens'
        unique_together = ['user', 'date']
        ordering = ['-date']

    def __str__(self):
        return f'{self.user.username} — {self.date} ({self.questions_answered}/{self.max_questions})'

    @property
    def remaining(self):
        return max(0, self.max_questions - self.questions_answered)

    @property
    def is_exhausted(self):
        return self.questions_answered >= self.max_questions

    def increment(self):
        self.questions_answered += 1
        self.save(update_fields=['questions_answered'])

    @classmethod
    def get_or_create_today(cls, user):
        """Récupère ou crée le quota du jour."""
        today = timezone.now().date()
        quota, created = cls.objects.get_or_create(
            user=user,
            date=today,
            defaults={
                'max_questions': getattr(settings, 'FREE_DAILY_QUESTIONS', 15)
            }
        )
        return quota

    @classmethod
    def can_answer(cls, user):
        """Vérifie si l'utilisateur peut encore répondre aujourd'hui."""
        if user.is_staff or user.is_superuser:
            return True, None
        if hasattr(user, 'profile') and user.profile.has_active_premium:
            return True, None
        quota = cls.get_or_create_today(user)
        return not quota.is_exhausted, quota


# Signal: create UserProfile when User is created
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()

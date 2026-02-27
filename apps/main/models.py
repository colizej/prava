from django.db import models


class Glossary(models.Model):
    """Glossaire trilingue des termes de conduite."""
    term = models.CharField('Terme (FR)', max_length=200)
    term_nl = models.CharField('Term (NL)', max_length=200, blank=True)
    term_ru = models.CharField('Термин (RU)', max_length=200, blank=True)

    definition = models.TextField('Définition (FR)')
    definition_nl = models.TextField('Definitie (NL)', blank=True)
    definition_ru = models.TextField('Определение (RU)', blank=True)

    category = models.CharField('Catégorie', max_length=100, blank=True)
    order = models.IntegerField('Ordre', default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Terme du glossaire'
        verbose_name_plural = 'Glossaire'
        ordering = ['order', 'term']

    def __str__(self):
        return self.term

    def get_term(self, lang='fr'):
        if lang == 'nl' and self.term_nl:
            return self.term_nl
        if lang == 'ru' and self.term_ru:
            return self.term_ru
        return self.term

    def get_definition(self, lang='fr'):
        if lang == 'nl' and self.definition_nl:
            return self.definition_nl
        if lang == 'ru' and self.definition_ru:
            return self.definition_ru
        return self.definition


class ContactMessage(models.Model):
    """Messages du formulaire de contact."""
    name = models.CharField('Nom', max_length=100)
    email = models.EmailField('Email')
    subject = models.CharField('Sujet', max_length=200)
    message = models.TextField('Message')
    is_read = models.BooleanField('Lu', default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Message de contact'
        verbose_name_plural = 'Messages de contact'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.name} — {self.subject}'

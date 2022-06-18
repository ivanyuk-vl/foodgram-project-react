from django.db.models import SlugField as DjangoModelsSlugField
from django.forms import SlugField as DjangoFormsSlugField

from .validators import validate_slug


class FormsSlugField(DjangoFormsSlugField):
    default_validators = [validate_slug]


class ModelsSlugField(DjangoModelsSlugField):
    default_validators = [validate_slug]

    def formfield(self, **kwargs):
        return super().formfield(**{
            'form_class': FormsSlugField,
            'allow_unicode': self.allow_unicode,
            **kwargs,
        })

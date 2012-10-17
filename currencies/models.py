from django.db import models
from django.utils.translation import gettext_lazy as _


class Currency(models.Model):
    code = models.CharField(_('code'), max_length=3)
    name = models.CharField(_('name'), max_length=35)
    symbol = models.CharField(_('symbol'), max_length=4, blank=True)
    factor = models.DecimalField(_('factor'), max_digits=10, decimal_places=4,
        help_text=_('Specifies the difference of the currency to default one.'))
    is_active = models.BooleanField(_('active'), default=True,
        help_text=_('The currency will be available.'))
    is_base = models.BooleanField(_('base'), default=False,
        help_text=_('Make this the base currency against which rates are calculated.'))
    is_default = models.BooleanField(_('default'), default=False,
        help_text=_('Make this the default user currency.'))

    class Meta:
        ordering = ('name', )
        verbose_name = _('currency')
        verbose_name_plural = _('currencies')

    def __unicode__(self):
        return self.code

    def save(self, **kwargs):
        # Make sure the base and default currencies are unique
        if self.is_base:
            Currency.objects.filter(is_base=True).update(is_base=False)
        if self.is_default:
            Currency.objects.filter(is_default=True).update(is_default=False)
        super(Currency, self).save(**kwargs)

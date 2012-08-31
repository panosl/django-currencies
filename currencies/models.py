from django.db import models
from django.utils.translation import gettext_lazy as _


class Currency(models.Model):
    code = models.CharField(_('code'), max_length=3)
    name = models.CharField(_('name'), max_length=35)
    symbol = models.CharField(_('symbol'), max_length=1)
    factor = models.DecimalField(_('factor'), max_digits=10, decimal_places=4,
        help_text=_('Specifies the difference of the currency to default one.'))
    is_active = models.BooleanField(_('active'), default=True,
        help_text=_('The currency will be available.'))
    is_default = models.BooleanField(_('default'), default=False,
        help_text=_('Make this the default currency.'))

    class Meta:
        verbose_name = _('currency')
        verbose_name_plural = _('currencies')

    def __unicode__(self):
        return self.code

    def save(self, **kwargs):
        # Make sure the default currency is unique
        if self.is_default:
            Currency.objects.filter(is_default=True).update(is_default=False)
        super(Currency, self).save(**kwargs)

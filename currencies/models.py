from django.db import models
from django.utils.translation import ugettext_lazy as _


class CurrencyManager(models.Manager):
    def active(self):
        return self.get_query_set().filter(is_active=True)


class Currency(models.Model):
    code = models.CharField(_('code'), max_length=3,
                            unique=True, db_index=True)
    name = models.CharField(_('name'), max_length=35,
                            unique=True, db_index=True)
    symbol = models.CharField(_('symbol'), max_length=4, blank=True,
                              db_index=True)
    factor = models.DecimalField(_('factor'), max_digits=30, decimal_places=10,
        help_text=_('Specifies the difference of the currency to default one.'))
    is_active = models.BooleanField(_('active'), default=True,
        help_text=_('The currency will be available.'))
    is_base = models.BooleanField(_('base'), default=False,
        help_text=_('Make this the base currency against which rates are calculated.'))
    is_default = models.BooleanField(_('default'), default=False,
        help_text=_('Make this the default user currency.'))

    objects = CurrencyManager()

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

    def to_base(self, price):
        from . import utils
        return utils.price_to_base(price, self)

    @classmethod
    def price_to_base(cls, price, code):
        return cls.objects.get(code__exact=code).to_base(price)

from django import template
from django.template.defaultfilters import stringfilter
from currencies.models import Currency
from currencies.utils import calculate_price

register = template.Library()


@register.filter(name='currency')
@stringfilter
def set_currency(value, arg):
    return calculate_price(value, arg)


class ChangeCurrencyNode(template.Node):

    def __init__(self, price, currency):
        self.price = template.Variable(price)
        self.currency = template.Variable(currency)

    def render(self, context):
        try:
            return calculate_price(self.price.resolve(context),
                self.currency.resolve(context))
        except template.VariableDoesNotExist:
            return ''


@register.tag(name='change_currency')
def change_currency(parser, token):
    contents = token.split_contents()
    show_symbols = False
    if len(contents) == 3:
        tag_name, current_price, new_currency = token.split_contents()
    elif len(contents) == 4:
        tag_name, current_price, new_currency, show_symbols = token.split_contents()
    else:
        tag_name = token.contents.split()[0]
        raise template.TemplateSyntaxError('%r tag requires at least two arguments' % (tag_name))

    node_class = ChangeCurrencyNodeWithSymbol if show_symbols else ChangeCurrencyNode
    return node_class(current_price, new_currency)


class ChangeCurrencyNodeWithSymbol(ChangeCurrencyNode):
    def render(self, context):
        value = super(ChangeCurrencyNodeWithSymbol, self).render(context)
        if value:
            currency = Currency.objects.get(
                code__exact=self.currency.resolve(context))
            value = u"%s%s %s" % (currency.pre_symbol, value, currency.symbol)
        return value
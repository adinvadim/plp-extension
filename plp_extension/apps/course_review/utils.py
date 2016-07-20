# coding: utf-8

from django.utils import timezone
from django.utils.translation import ugettext as _, ungettext


def time_passed_since(date):
    """
    для преобразования прошедшей даты в слова, например "вчера", "2 недели назад"
    """
    td = (timezone.now() - date).days
    if td / 365:
        return ungettext(u'%(num)s год назад', u'%(num)s лет назад', td/365) % {'num': td/365}
    elif td / 30:
        return ungettext(u'%(num)s месяц назад', u'%(num)s месяцев назад', td/30) % {'num': td/30}
    elif td / 7:
        return ungettext(u'%(num)s неделя назад', u'%(num)s недель назад', td/7) % {'num': td/7}
    elif td in range(2, 7):
        return ungettext(u'%(num)s день назад', u'%(num)s дней назад', td) % {'num': td}
    elif td == 1:
        return _(u'вчера')
    else:
        return _(u'сегодня')

from django.template import Library


register = Library()


@register.filter(name='add_class')
def add_class(field, class_attr):
    return field.as_widget(attrs={'class': class_attr})


@register.filter(name='anonymize')
def anonymize(value, hide):
    if hide:
        return value[0] + "*" * (len(value) - 1)
    return value

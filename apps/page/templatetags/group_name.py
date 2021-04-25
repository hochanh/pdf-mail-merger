from django.template import Library


register = Library()


@register.filter(name='group_name')
def group_name(group):
    if '|' in group.name:
        return group.name.split('|')[1]
    return group.name

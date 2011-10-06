from django.template import Library

register = Library()

@register.filter
def get_chr(value):
  return chr(value + ord('a'))


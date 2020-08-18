from django import template

register = template.Library()

@register.filter
def modulo(num):
    return num % 2

@register.filter
def add(num, num2):
    return num + num2
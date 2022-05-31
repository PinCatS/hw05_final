from django.conf import settings
from django.core.paginator import Paginator


def get_page_from_paginator(
    request, items, posts_per_page=settings.POSTS_PER_PAGE
):
    paginator = Paginator(items, posts_per_page)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj

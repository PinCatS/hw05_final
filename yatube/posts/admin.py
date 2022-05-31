from django.contrib import admin

from .models import Comment, Follow, Group, Post


class GroupAdmin(admin.ModelAdmin):
    list_display = (
        'slug',
        'title',
        'description',
    )
    search_fields = ('slug', 'title')


class PostAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'text',
        'pub_date',
        'author',
        'group',
    )
    search_fields = ('text',)
    list_filter = ('pub_date',)
    empty_value_display = '-пусто-'
    list_editable = ('group',)


class FollowAdmin(admin.ModelAdmin):
    list_display = ('pk', 'user', 'author')


class CommentAdmin(admin.ModelAdmin):
    list_display = ('pk', 'author', 'post')


admin.site.register(Group, GroupAdmin)
admin.site.register(Post, PostAdmin)
admin.site.register(Follow, FollowAdmin)
admin.site.register(Comment, CommentAdmin)

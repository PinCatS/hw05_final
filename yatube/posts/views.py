from core import utils
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User


@cache_page(20, key_prefix='index_page')
def index(request):
    template = 'posts/index.html'
    posts = Post.objects.all()
    page_obj = utils.get_page_from_paginator(request, posts)
    context = {'page_obj': page_obj}
    return render(request, template, context)


@login_required
def post_create(request):
    template = 'posts/create_post.html'
    user = request.user
    form = PostForm(request.POST or None, files=request.FILES or None)
    context = {'is_edit': False, 'form': form}

    if request.method == 'POST':
        if form.is_valid():
            new_post = form.save(commit=False)
            new_post.author = user
            new_post.save()
            return redirect('posts:profile', user.username)

    return render(request, template, context)


@login_required
def post_edit(request, post_id):
    template = 'posts/create_post.html'
    post = get_object_or_404(Post, pk=post_id)
    user = request.user
    form = PostForm(
        request.POST or None, files=request.FILES or None, instance=post
    )
    context = {'is_edit': True, 'post_id': post_id, 'form': form}

    if post.author.username != user.username:
        return redirect('posts:post_detail', post_id)

    if request.method == 'POST':
        if form.is_valid():
            form.save()
            return redirect('posts:post_detail', post_id)

    return render(request, template, context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)

    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


def group_posts(request, slug):
    template = 'posts/group_list.html'
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    page_obj = utils.get_page_from_paginator(request, posts)
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, template, context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    user = request.user
    following = False
    if user.is_authenticated:
        following = author.following.filter(user=user).exists()
    posts = author.posts.all()
    page_obj = utils.get_page_from_paginator(request, posts)
    context = {
        'author': author,
        'page_obj': page_obj,
        'following': following,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    comments = post.comments.all()
    form = CommentForm()
    context = {'post': post, 'comments': comments, 'form': form}
    return render(request, 'posts/post_detail.html', context)


@login_required
def follow_index(request):
    authors = map(lambda f: f.author, request.user.follower.all())
    posts = Post.objects.filter(author__in=authors)
    page_obj = utils.get_page_from_paginator(request, posts)
    context = {'page_obj': page_obj}
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    user = request.user
    if user.username != username:
        author = get_object_or_404(User, username=username)
        Follow.objects.create(user=user, author=author)
    return redirect('posts:profile', username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    request.user.follower.filter(author=author).delete()
    return redirect('posts:profile', username)

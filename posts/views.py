from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect

from .forms import PostForm, CommentForm
from .models import Post, Group, User, Comment, Follow


def index(request):
    post_list = Post.objects.all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'index.html',
                  {'page': page, 'paginator': paginator})


def group_post(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.group_posts.all()
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'posts/group.html',
                  {'group': group,
                   'page': page,
                   'paginator': paginator})


@login_required
def new_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST or None,
                        files=request.FILES or None)

        if form.is_valid():
            post_new = form.save(commit=False)
            post_new.author = request.user
            post_new.save()
            return redirect('index')

        return render(request, 'posts/new-post.html', {'form': form})

    form = PostForm()
    return render(request, 'posts/new-post.html', {'form': form})


def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts = author.author_posts.filter(author=author)
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    following = None
    if author.following.filter(user=request.user.id):
        following = True

    return render(request, 'posts/profile.html',
                  {'author': author, 'posts': posts, 'page': page,
                   'paginator': paginator, 'username': username,
                   'following': following})


def post_view(request, username, post_id):
    author = get_object_or_404(User, username=username)
    post = get_object_or_404(Post, author=author, id=post_id)
    form = CommentForm()
    items = post.comments.filter(post=post)
    following = None
    if author.following.filter(user=request.user.id):
        following = True
    return render(request,
                  'posts/post.html',
                  {'post': post, 'author': author,
                   'form': form, 'items': items,
                   'following': following})


@login_required
def post_edit(request, username, post_id):
    author = get_object_or_404(User, username=username)
    editable_post = get_object_or_404(Post, author=author, id=post_id)
    if request.user != author:
        return redirect('post_view',
                        username=request.user.username,
                        post_id=post_id)

    form = PostForm(request.POST or None,
                    files=request.FILES or None,
                    instance=editable_post)

    if request.method == 'POST':
        if form.is_valid():
            form.save()
            return redirect('post_view',
                            username=request.user.username,
                            post_id=post_id)

    return render(request, 'posts/new-post.html',
                  {'form': form, 'author': author, 'post': editable_post})


@login_required
def add_comment(request, username, post_id):
    post = get_object_or_404(Post, id=post_id)

    if request.method == 'POST':
        form = CommentForm(request.POST)

        if form.is_valid():
            new_comment = form.save(commit=False)
            new_comment.author = request.user
            new_comment.post = post
            new_comment.save()
            return redirect('post_view', username=username, post_id=post_id)


@login_required
def follow_index(request):
    follow = Follow.objects.filter(user=request.user).values('author')
    posts = Post.objects.select_related('author').filter(author__in=follow)
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request,
                  'posts/follow.html',
                  {'page': page,
                   'paginator': paginator})


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    already_followed = Follow.objects.filter(
        user=request.user.id,
        author=author.id).exists()

    if author.id != request.user.id and not already_followed:
        Follow.objects.create(user=request.user, author=author)

    return redirect('profile', username=username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    already_followed = Follow.objects.filter(user=request.user.id,
                                             author=author.id).exists()

    if already_followed:
        Follow.objects.filter(user=request.user.id,
                              author=author.id).delete()

    return redirect('profile', username)


def page_not_found(request, exception):
    return render(request,
                  'misc/404.html',
                  {'path': request.path},
                  status=404)


def server_error(request):
    return render(request,
                  'misc/500.html',
                  status=500)

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render, get_object_or_404, redirect, reverse
from django.db.models import Count, Q
from django.views import View

from .forms import CommentForm, PostForm
from .models import Post, Author, PostView, BookmarkPost
from marketing.models import Singup

def get_authour(user):
    qs = Author.objects.filter(user=user)
    if qs.exists():
        return qs[0]
    return None

def search(request):
    queryset = Post.objects.all()
    query = request.GET.get("q")
    if query:
        queryset = queryset.filter(
            Q(title__icontains=query) | 
            Q(overview__icontains=query)
        ).distinct()
    context = {
        "queryset" : queryset
    }

    return render(request, "search_result.html", context)

def get_category_count():
    queryset = Post \
            .objects \
            .values("categories__title")\
            .annotate(Count('categories__title'))
    return queryset 

def index(request):
    featured = Post.objects.filter(featured=True)
    latest   = Post.objects.order_by("-timestamp")[0:3]
    if request.method == "POST":
        email   = request.POST["email"]
        new_sign = Singup()
        new_sign.email = email
        new_sign.save()
    context = {
        'object_list': featured,
        'latest'     : latest
    }
    return render(request, 'index.html', context)

def blog(request):
    categories_count =   get_category_count()
    most_recent = Post.objects.order_by("-timestamp")[:3]
    post_list = Post.objects.all()
    paginator = Paginator(post_list, 6)
    page_request = 'page'
    page = request.GET.get(page_request)
    try:
        paginator_queryset = paginator.page(page)
    except PageNotAnInteger:
        paginator_queryset = paginator.page(1)
    except EmptyPage:
        paginator_queryset = paginator.page(paginator.num_pages)
    

    context = {
        'queryset': paginator_queryset,
        'most_recent': most_recent,
        'page_request': page_request,
        'categories_count': categories_count
    }
    return render(request, 'blog.html', context)

def post(request, id):
    most_recent = Post.objects.order_by("-timestamp")[:3]
    categories_count =   get_category_count()
    post    = get_object_or_404(Post, id=id)

    if request.user.is_authenticated:
        PostView.objects.get_or_create(user=request.user, post=post)
    
    form = CommentForm(request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            form.instance.user = request.user
            form.instance.post = post
            form.save()
            return redirect(reverse("post-detail", kwargs={
                "id": post.pk
            }))
    context = {
        'form': form,
        'post': post,
        'most_recent': most_recent,
        'categories_count': categories_count
    }
    return render(request, 'post.html', context)

def about(request):
    return render(request, 'about.html', {}) 

def post_create(request):
    title = 'Create'
    form    = PostForm(request.POST or None, request.FILES or None)
    author = get_authour(request.user)
    if request.method == "POST":
        if form.is_valid():
            form.instance.author = author
            form.save()
            return redirect(reverse("post-detail", kwargs={
                'id': form.instance.id
            }))
    context = {
        'title': title,
        'form': form
    }
    return render(request, "post_create.html", context) 

def post_update(request, id):
    title = "Update"
    post = get_object_or_404(Post, id=id)
    form    = PostForm(request.POST or None, request.FILES or None, instance=post)
    author = get_authour(request.user)
    if request.method == "POST":
        if form.is_valid():
            form.instance.author = author
            form.save()
            return redirect(reverse("post-detail", kwargs={
                'id': form.instance.id
            }))
    context = {
        "title": title,
        'form': form
    }
    return render(request, "post_create.html", context)

def post_delete(request, id):
    post = get_object_or_404(Post, id=id)
    post.delete()
    return redirect(reverse("post-list"))

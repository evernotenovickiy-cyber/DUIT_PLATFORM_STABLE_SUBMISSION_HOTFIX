from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import PostForm
from .models import Post


def index(request):
    posts = Post.objects.filter(is_published=True).select_related("author", "author__profile")
    city = request.GET.get("city", "").strip()
    kind = request.GET.get("kind", "").strip()
    q = request.GET.get("q", "").strip()
    if city:
        posts = posts.filter(city=city)
    if kind:
        posts = posts.filter(kind=kind)
    if q:
        posts = posts.filter(Q(title__icontains=q) | Q(excerpt__icontains=q) | Q(body__icontains=q))
    page_obj = Paginator(posts, 12).get_page(request.GET.get("page"))
    cities = list(Post.objects.filter(is_published=True).exclude(city="").values_list("city", flat=True).distinct().order_by("city"))
    return render(request, "journal/index.html", {"page_obj": page_obj, "cities": cities, "active_city": city, "active_kind": kind, "query": q, "kinds": Post.Kind.choices})


def detail(request, slug):
    post = get_object_or_404(Post.objects.select_related("author", "author__profile"), slug=slug, is_published=True)
    related = Post.objects.filter(is_published=True, kind=post.kind).exclude(pk=post.pk)[:3]
    return render(request, "journal/detail.html", {"post": post, "related": related})


@login_required
def create(request):
    if request.method == "POST":
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            messages.success(request, "Публикация добавлена в Журнал DUIT.")
            return redirect(post.get_absolute_url())
    else:
        form = PostForm(initial={"city": request.user.profile.city})
    return render(request, "journal/form.html", {"form": form})

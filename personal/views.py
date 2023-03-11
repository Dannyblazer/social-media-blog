from django.shortcuts import render, redirect
from blog.models import BlogPost
from django.conf import settings
from operator import attrgetter
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from blog.views import get_blog_queryset
import requests
# Create your views here.
BLOG_POSTS_PER_PAGE = 10

def home_view(request):
    query = ""
    if request.GET:
        query = request.GET.get('q', '')
    blog_posts = sorted(get_blog_queryset(query), key=attrgetter('date_published'), reverse=True)

    # Pagination
    page = request.GET.get('page', 1)
    blog_posts_paginator = Paginator(blog_posts, BLOG_POSTS_PER_PAGE)

    try:
        blog_posts = blog_posts_paginator.page(page)
    except PageNotAnInteger:
        blog_posts = blog_posts_paginator.page(BLOG_POSTS_PER_PAGE)
    except EmptyPage:
        blog_posts = blog_posts_paginator.page(blog_posts_paginator.num_pages)

    return render(request, 'snippets/home.html', context={"blog_posts":blog_posts, "query":str(query), "is_home": True})

# News Search

'''def get_blog_queryset(query=None):
	queryset = []
	queries = query.split(" ")
	for q in queries:
		posts = BlogPost.objects.filter(
			Q(title__contains=q)|
			Q(body__icontains=q)
			).distinct()
		for post in posts:
			queryset.append(post)

	# create unique set and then convert to list
	return list(set(queryset)) '''

def news_articles(request):
    api_key = 'e418393757ed4fc298176650cf07b061'
    url = f'https://newsapi.org/v2/top-headlines?q=entertainment&apiKey={api_key}'
    response = requests.get(url)
    news_data = response.json()
    articles = news_data['articles']
    blog_posts = articles

    # Pagination
    page = request.GET.get('page', 1)
    blog_posts_paginator = Paginator(blog_posts, BLOG_POSTS_PER_PAGE)

    try:
        blog_posts = blog_posts_paginator.page(page)
    except PageNotAnInteger:
        blog_posts = blog_posts_paginator.page(BLOG_POSTS_PER_PAGE)
    except EmptyPage:
        blog_posts = blog_posts_paginator.page(blog_posts_paginator.num_pages)
    
    return render(request, 'snippets/news_articles.html', {'blog_posts' : articles})

def public_chat(request):
    context = {}
    context['debug_model'] = settings.DEBUG
    context['room_id'] = 1
    return render(request, "snippets/public_chat.html", context)


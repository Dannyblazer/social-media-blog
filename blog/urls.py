from django.urls import path
from blog.views import create_blog_view, detail_blog_view, edit_blog_view, blog_like, create_comment, delete_comment, comments

app_name = 'blog'

urlpatterns = [
    path('create/', create_blog_view, name="create"),
    path('comments/<int:blog_post_id>', comments, name='comments'),
    path('<com_id>/delete_com', delete_comment, name="delete_comment"),
    path('<slug>/', detail_blog_view, name="detail"),
    path('<blog_id>/create_com/', create_comment, name="create_comment"),
    path('<slug>/edit', edit_blog_view, name="edit"),
    path('like/<pk>', blog_like, name="like"),
]

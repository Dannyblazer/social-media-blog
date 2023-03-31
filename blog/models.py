from django.db import models
from django.db.models.signals import pre_save, post_delete
from django.utils.text import slugify
from django.utils import timezone
from django.conf import settings
from django.dispatch import receiver
from users.models import Account
import math

# Create your models here.

def upload_location(instance, filename):
    file_path = 'blog/{author_id}/{title}-{filename}'.format(
        author_id=str(instance.author.id), title=str(instance.title), filename=filename
    )
    return file_path


class BlogPost(models.Model):
    title           = models.CharField(max_length=50, null=False, blank=False)
    body            = models.TextField(max_length=5000, null=False, blank=False)
    image           = models.ImageField(upload_to=upload_location, null=False, blank=False)
    date_published  = models.DateTimeField(auto_now_add=True, verbose_name="date published")
    date_updated    = models.DateTimeField(auto_now=True, verbose_name="date updated")
    author          = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    slug            = models.SlugField(blank=True, unique=True)
    category        = models.CharField(max_length=30, default='coding')
    likes           = models.ManyToManyField(Account, related_name='blog_posts')

    def __str__(self):
        return self.title
    
    def whenpublished(self):
        now = timezone.now()

        diff = now-self.date_published
        if diff.days == 0 and diff.seconds >= 0 and diff.seconds < 60:
            seconds=diff.seconds
            if seconds==1:
                return str(seconds)+" second ago"
            else:
                return str(seconds)+" seconds ago"
        if diff.days == 0 and diff.seconds >= 60 and diff.seconds < 3600:
            minutes=math.floor(diff.seconds/60)
            if minutes == 1:
                return str(minutes)+" minute ago"
            else:
                return str(minutes)+" minutes ago"
        if diff.days == 0 and diff.seconds >= 3600 and diff.seconds < 84600:
            hours = math.floor(diff.seconds/3600)
            if hours ==1:
                return str(hours)+" hour ago"
            else:
                return str(hours)+" hours ago"
        # 1 day to 30 days(months and years)
        if diff.days >=1 and diff.days < 30:
            days = diff.days
            if diff.days ==1:
                return str(days)+" day ago"
            else:
                return str(days)+" days ago"
        if diff.days >= 30 and diff.days <365:
            months=math.floor(diff.days/30)
            if months ==1:
                return str(months)+" month ago"
            else:
                return str(months)+" months ago"
        if diff.days > 365:
            years = math.floor(diff.days/365)
            if years ==1:
                return str(years)+" year ago"
            else:
                return str(years)+" years ago"

class Comment(models.Model):
    blogpost = models.ForeignKey(BlogPost, related_name= "comment", on_delete=models.CASCADE)
    body = models.TextField()
    author = models.ForeignKey(Account, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.body
    
    def whenpublished(self):
        now = timezone.now()

        diff = now-self.created_at
        if diff.days == 0 and diff.seconds >= 0 and diff.seconds < 60:
            seconds=diff.seconds
            if seconds==1:
                return str(seconds)+" second ago"
            else:
                return str(seconds)+" seconds ago"
        if diff.days == 0 and diff.seconds >= 60 and diff.seconds < 3600:
            minutes=math.floor(diff.seconds/60)
            if minutes == 1:
                return str(minutes)+" minute ago"
            else:
                return str(minutes)+" minutes ago"
        if diff.days == 0 and diff.seconds >= 3600 and diff.seconds < 84600:
            hours = math.floor(diff.seconds/3600)
            if hours ==1:
                return str(hours)+" hour ago"
            else:
                return str(hours)+" hours ago"
        # 1 day to 30 days(months and years)
        if diff.days >=1 and diff.days < 30:
            days = diff.days
            if diff.days ==1:
                return str(days)+" day ago"
            else:
                return str(days)+" days ago"
        if diff.days >= 30 and diff.days <365:
            months=math.floor(diff.days/30)
            if months ==1:
                return str(months)+" month ago"
            else:
                return str(months)+" months ago"
        if diff.days > 365:
            years = math.floor(diff.days/365)
            if years ==1:
                return str(years)+" year ago"
            else:
                return str(years)+" years ago"
    

@receiver(post_delete, sender=BlogPost)
def submission_delete(sender, instance, **Kwargs):
    instance.image.delete(False)

def pre_save_blog_post_receiver(sender, instance, *args, **Kwargs):
    if not instance.slug:
        instance.slug = slugify(instance.author.username + "-" + instance.title)

pre_save.connect(pre_save_blog_post_receiver, sender=BlogPost)

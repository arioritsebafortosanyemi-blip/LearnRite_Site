from django.db import models
from django.contrib.auth.models import User
from django.contrib import auth

class Author(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField()

    def __str__(self):
        return self.user

class Post(models.Model):
    title = models.CharField(max_length=200)
    image = models.ImageField(verbose_name="Image of Blog Post", upload_to="blog/blogpost_image")
    slug = models.SlugField(unique=True)
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    content = models.TextField(help_text="The content of the post.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

class Comment(models.Model):
    content = models.TextField \
        (help_text="The comment text.")

    rating = models.IntegerField \
        (help_text="The ratings the commenter has given")

    date_created = models.DateTimeField \
        (auto_now_add=True,\
         help_text="The date and time the comment was created")

    date_edited = models.DateTimeField \
        (null=True,\
         help_text="The date and time the comment was last edited.")

    creator = models.ForeignKey \
        (auth.get_user_model(), on_delete=models.CASCADE)

    post = models.ForeignKey \
        (Post, on_delete=models.CASCADE,\
         help_text="The book that this review is for.")
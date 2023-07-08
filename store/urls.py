from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [path('', views.index, name='index'),\
               path('aboutus/', views.aboutUs, name='aboutus'),
               path('services/', views.services, name='services'),
               path('givingback/',views.givingback, name='givingback'),
               path('books/', views.books, name='books'),
               path('faqs/', views.faqs, name='faqs'),
               path('books/<int:pk>', views.book_detail, name = 'book_detail'),
               path('authors/', views.authors, name = 'authors'),
               path('authors/<int:pk>', views.author_detail, name = 'author_detail'),
               path('search/', views.search_result, name='search'),
               path('books/pre-school/', views.pre_school, name='pre-school'),
               path('books/primary-school/', views.primary_school, name='primary-school'),
               path('books/high-school/', views.high_school, name='high-school'),
               path('books/exam-study/', views.exam_study_school, name='exam-study'),
               path('books/story-books', views.story_books_school, name='story-books')
               ]
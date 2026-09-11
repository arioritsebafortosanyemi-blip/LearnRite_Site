from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.views.decorators.http import require_POST
from .models import Book, Contributor, Review
from django.db.models import Q
from .utils import average_rating, random_books, random_book
from .forms import SearchForm, PreSchoolBookFilterForm, PrimarySchoolBookFilterForm, HighSchoolBookFilterForm, ExamStudyBookFilterForm, StoryBookFilterForm, ReviewForm
from django.core.paginator import Paginator

from orders.models import Order, OrderItem


def index(request):
    books = random_books(Book.objects.all(), 20)
    author= Contributor.objects.first()
    pre_school = random_books(Book.objects.filter(category__name='PRE-SCHOOL'), 3)
    p_school = random_books(Book.objects.filter(category__name='PRIMARY SCHOOL'), 3)
    h_school = random_books(Book.objects.filter(category__name='HIGH SCHOOL'), 3)
    exam_study = random_books(Book.objects.filter(category__name='EXAM & STUDY'), 3)
    story_books = random_books(Book.objects.filter(category__name='STORY BOOKS'), 3)
    form = SearchForm(request.GET)

    context = {'books': books,
               'pre_school': pre_school,
               'p_school': p_school,
               'h_school': h_school,
               'exam_study': exam_study,
               'story_books': story_books,
               'author':author,
               'form': form}
    return render(request, "store/index.html", context)

def aboutUs(request):
    form = SearchForm(request.GET)

    return render(request, "store/aboutus.html", {'form': form})

def services(request):
    form = SearchForm(request.GET)

    return render(request, "store/services.html", {'form': form})

def givingback(request):
    form = SearchForm(request.GET)

    return render(request, "store/givingback.html", {'form': form})

def faqs(request):
    form = SearchForm(request.GET)

    return render(request, 'store/faqs.html', {'form': form})

def authors(request):
    authors = Contributor.objects.first()
    form = SearchForm(request.GET)

    context = {'authors':authors,
               'form':form }
    return render(request, 'store/authors.html', context)

def author_detail(request,pk):
    author = get_object_or_404(Contributor, pk=pk)
    related_books = random_books(author.book_set.all(), 3)
    form = SearchForm(request.GET)

    context = {'author':author,
               "form": form,
               "related_books":related_books}
    return render(request, 'store/author_detail.html', context)

def books(request):
    best_seller = random_books(Book.objects.all(), 4)
    pre_school = random_books(Book.objects.filter(category__name='PRE-SCHOOL'), 4)
    p_school = random_books(Book.objects.filter(category__name='PRIMARY SCHOOL'), 4)
    h_school = random_books(Book.objects.filter(category__name='HIGH SCHOOL'), 4)
    other_cat = random_books(Book.objects.filter(Q(category__name ='EXAM & STUDY') | Q(category__name='STORY BOOKS')), 12)
    form = SearchForm(request.GET)

    context = {'best_seller':best_seller,
               'pre_school': pre_school,
               'p_school': p_school,
               'h_school': h_school,
               'other_cat': other_cat,
               "form": form}
    return render(request, 'store/books.html', context)

def book_detail(request, pk):
    book = get_object_or_404(Book.objects.prefetch_related('contributors', 'prices', 'review_set'), pk=pk)
    reviews = book.review_set.all()
    related_books = Book.objects.filter( Q(subcategory=book.subcategory) | Q(contributors__in=book.contributors.all())).exclude(pk=pk).prefetch_related('contributors', 'prices', 'review_set').distinct()[:4]
    form = SearchForm(request.GET)

    if reviews.exists():
        book_rating = average_rating( [review.rating for review in reviews ])
        context = {
            "book": book,
            "rating": book_rating,
            "reviews": reviews,
            "related_books": related_books,
            "form": form
        }
    else:
        context = {
            "book": book,
            "rating": None,
            "reviews": None,
            "related_books": related_books,
            "form": form
        }

    return render(request, 'store/book_detail.html', context)

def search_result(request):
    search_text = request.GET.get('search', '')
    search_cat = request.GET.get('search_in')
    form = SearchForm(request.GET)
    results = []

    if form.is_valid() and form.cleaned_data['search']:
        search = form.cleaned_data['search']
        search_in = form.cleaned_data.get('search_in') or 'contributor'

        if search_in == 'all':
            # Query for books matching the title
            books = Book.objects.filter(title__icontains=search)
            results.extend(books)

            # Query for contributors matching first names
            fname_contributors = Contributor.objects.filter(first_names__icontains=search)
            for contributor in fname_contributors:
                results.extend(contributor.book_set.all())

            # Query for contributors matching last names
            lname_contributors = Contributor.objects.filter(last_names__icontains=search)
            for contributor in lname_contributors:
                results.extend(contributor.book_set.all())

        elif search_in == 'title':
            books = Book.objects.filter(title__icontains=search)
            results.extend(books)

        elif search_in == 'contributor':
            fname_contributors = Contributor.objects.filter(first_names__icontains=search)
            for contributor in fname_contributors:
                results.extend(contributor.book_set.all())

            lname_contributors = Contributor.objects.filter(last_names__icontains=search)
            for contributor in lname_contributors:
                results.extend(contributor.book_set.all())

        paginator = Paginator(results, 10)
        page = request.GET.get('page', 1)

        try:
            search_results = paginator.page(page)
        except Exception:
            search_results = paginator.page(1)

        return render(request, 'store/search-results.html',
                      {"form": form, "search_text": search_text, "books": search_results, "search_cat":search_cat})

def pre_school(request):
    form = SearchForm(request.GET)
    filter_form = PreSchoolBookFilterForm(request.GET)

    class_query = request.GET.getlist('filter_option')

    books = Book.objects.filter(category__name='PRE-SCHOOL').prefetch_related('contributors', 'prices', 'review_set')
    if len(class_query) == 1:
        books = books.filter(subcategory__name=class_query[0])
    elif len(class_query) > 1:
        books = books.filter(subcategory__name__in=class_query)

    best_seller = random_book(Book.objects.filter(category__name='PRE-SCHOOL'))
    paginator = Paginator(books, 9)

    page = request.GET.get('page')
    items = paginator.get_page(page)

    return render(request, 'store/pre-school.html', {"filter_form":filter_form,"form":form, "items":items, "best_seller":best_seller})


def primary_school(request):
    form = SearchForm(request.GET)
    filter_form = PrimarySchoolBookFilterForm(request.GET)

    class_query = request.GET.getlist('filter_option')

    books = Book.objects.filter(category__name='PRIMARY SCHOOL').prefetch_related('contributors', 'prices', 'review_set')
    if len(class_query) == 1:
        books = books.filter(subcategory__name=class_query[0])
    elif len(class_query) > 1:
        books = books.filter(subcategory__name__in=class_query)

    best_seller = random_book(Book.objects.filter(category__name='PRIMARY SCHOOL'))
    paginator = Paginator(books, 9)

    page = request.GET.get('page')
    items = paginator.get_page(page)

    return render(request, 'store/primary-school.html', {"filter_form":filter_form,"form":form, "items":items, "best_seller":best_seller})

def high_school(request):
    form = SearchForm(request.GET)
    filter_form = HighSchoolBookFilterForm(request.GET)

    class_query = request.GET.getlist('filter_option')

    books = Book.objects.filter(category__name='HIGH SCHOOL').prefetch_related('contributors', 'prices', 'review_set')
    if len(class_query) == 1:
        books = books.filter(subcategory__name=class_query[0])
    elif len(class_query) > 1:
        books = books.filter(subcategory__name__in=class_query)

    best_seller = random_book(Book.objects.filter(category__name='HIGH SCHOOL'))
    paginator = Paginator(books, 9)

    page = request.GET.get('page')
    items = paginator.get_page(page)

    return render(request, 'store/high-school.html', {"filter_form":filter_form,"form":form, "items":items, "best_seller":best_seller})

def exam_study_school(request):
    form = SearchForm(request.GET)
    filter_form = ExamStudyBookFilterForm(request.GET)

    exam_query = request.GET.getlist('filter_option')

    books = Book.objects.filter(category__name='EXAM & STUDY').prefetch_related('contributors', 'prices', 'review_set')
    if len(exam_query) == 1:
        books = books.filter(subcategory__name=exam_query[0])
    elif len(exam_query) > 1:
        books = books.filter(subcategory__name__in=exam_query)

    best_seller = random_book(Book.objects.filter(category__name='EXAM & STUDY'))
    paginator = Paginator(books, 9)

    page = request.GET.get('page')
    items = paginator.get_page(page)

    return render(request, 'store/exam-study.html', {"filter_form":filter_form,"form":form, "items":items, "best_seller":best_seller})


def story_books_school(request):
    #variables to add forms to context
    form = SearchForm(request.GET)
    filter_form = StoryBookFilterForm(request.GET)

    #retrieving information from
    genre_query = request.GET.getlist('filter_option')

    books = Book.objects.filter(category__name='STORY BOOKS').prefetch_related('contributors', 'prices', 'review_set')
    if len(genre_query) == 1:
        books = books.filter(subcategory__name=genre_query[0])
    elif len(genre_query) > 1:
        books = books.filter(subcategory__name__in=genre_query)

    best_seller = random_book(Book.objects.filter(category__name='STORY BOOKS'))
    paginator = Paginator(books, 9)

    page = request.GET.get('page')
    items = paginator.get_page(page)

    return render(request, 'store/story-books.html', {"filter_form":filter_form,"form":form, "items":items, "best_seller":best_seller})


@login_required
@require_POST
def review_create(request, pk):
    book = get_object_or_404(Book, pk=pk)
    has_purchased = OrderItem.objects.filter(
        order__user=request.user,
        order__status__in=[Order.Status.PAID, Order.Status.FULFILLED],
        book=book,
    ).exists()
    if not has_purchased:
        messages.error(request, "You can only rate books you've purchased.")
        return redirect('profile')

    review_form = ReviewForm(request.POST)
    if not review_form.is_valid():
        messages.error(request, "Please pick a star rating before submitting.")
        return redirect('profile')

    review, created = Review.objects.update_or_create(
        book=book, creator=request.user,
        defaults={
            'rating': review_form.cleaned_data['rating'],
            'content': review_form.cleaned_data['content'],
        },
    )
    if not created:
        review.date_edited = timezone.now()
        review.save(update_fields=['date_edited'])

    messages.success(request, f'Thanks for rating "{book.title}"!')
    return redirect('profile')
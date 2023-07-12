from django.shortcuts import render, get_object_or_404
from .models import Book, Contributor
from django.db.models import Q
from .utils import average_rating
from .forms import SearchForm, PreSchoolBookFilterForm, PrimarySchoolBookFilterForm, HighSchoolBookFilterForm, ExamStudyBookFilterForm, StoryBookFilterForm
from django.core.paginator import Paginator


def index(request):
    books = Book.objects.order_by('?')[:20]
    author= Contributor.objects.first()
    pre_school = Book.objects.filter(category__name='PRE-SCHOOL').order_by('?')[:3]
    p_school = Book.objects.filter(category__name='PRIMARY SCHOOL').order_by('?')[:3]
    h_school = Book.objects.filter(category__name='HIGH SCHOOL').order_by('?')[:3]
    exam_study = Book.objects.filter(category__name='EXAM & STUDY').order_by('?')[:3]
    story_books = Book.objects.filter(category__name='STORY BOOKS').order_by('?')[:3]
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
    related_books = author.book_set.all().order_by('?')[:3]
    form = SearchForm(request.GET)

    context = {'author':author,
               "form": form,
               "related_books":related_books}
    return render(request, 'store/author_detail.html', context)

def books(request):
    best_seller = Book.objects.order_by('?')[:4]
    pre_school = Book.objects.filter(category__name='PRE-SCHOOL').order_by('?')[:4]
    p_school = Book.objects.filter(category__name='PRIMARY SCHOOL').order_by('?')[:4]
    h_school = Book.objects.filter(category__name='HIGH SCHOOL').order_by('?')[:4]
    other_cat = Book.objects.filter(Q(category__name ='EXAM & STUDY') | Q(category__name='STORY BOOKS')).order_by('?')[:12]
    form = SearchForm(request.GET)

    context = {'best_seller':best_seller,
               'pre_school': pre_school,
               'p_school': p_school,
               'h_school': h_school,
               'other_cat': other_cat,
               "form": form}
    return render(request, 'store/books.html', context)

def book_detail(request, pk):
    book = get_object_or_404(Book, pk=pk)
    reviews = book.review_set.all()
    related_books = Book.objects.filter( Q(subcategory=book.subcategory) | Q(contributors__in=book.contributors.all())).exclude(pk=pk)[:4]
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

    books = Book.objects.filter(category__name='PRE-SCHOOL')
    if len(class_query) == 1:
        books = books.filter(subcategory__name=class_query[0])
    elif len(class_query) > 1:
        books = books.filter(subcategory__name__in=class_query)

    best_seller = Book.objects.filter(category__name='PRE-SCHOOL').order_by('?').first()
    paginator = Paginator(books, 9)

    page = request.GET.get('page')
    items = paginator.get_page(page)

    return render(request, 'store/pre-school.html', {"filter_form":filter_form,"form":form, "items":items, "best_seller":best_seller})


def primary_school(request):
    form = SearchForm(request.GET)
    filter_form = PrimarySchoolBookFilterForm(request.GET)

    class_query = request.GET.getlist('filter_option')

    books = Book.objects.filter(category__name='PRIMARY SCHOOL')
    if len(class_query) == 1:
        books = books.filter(subcategory__name=class_query[0])
    elif len(class_query) > 1:
        books = books.filter(subcategory__name__in=class_query)

    best_seller = Book.objects.filter(category__name='PRIMARY SCHOOL').order_by('?').first()
    paginator = Paginator(books, 9)

    page = request.GET.get('page')
    items = paginator.get_page(page)

    return render(request, 'store/primary-school.html', {"filter_form":filter_form,"form":form, "items":items, "best_seller":best_seller})

def high_school(request):
    form = SearchForm(request.GET)
    filter_form = HighSchoolBookFilterForm(request.GET)

    class_query = request.GET.getlist('filter_option')

    books = Book.objects.filter(category__name='HIGH SCHOOL')
    if len(class_query) == 1:
        books = books.filter(subcategory__name=class_query[0])
    elif len(class_query) > 1:
        books = books.filter(subcategory__name__in=class_query)

    best_seller = Book.objects.filter(category__name='HIGH SCHOOL').order_by('?').first() or []
    paginator = Paginator(books, 9)

    page = request.GET.get('page')
    items = paginator.get_page(page)

    return render(request, 'store/high-school.html', {"filter_form":filter_form,"form":form, "items":items, "best_seller":best_seller})

def exam_study_school(request):
    form = SearchForm(request.GET)
    filter_form = ExamStudyBookFilterForm(request.GET)

    exam_query = request.GET.getlist('filter_option')

    books = Book.objects.filter(category__name='EXAM & STUDY')
    if len(exam_query) == 1:
        books = books.filter(subcategory__name=exam_query[0])
    elif len(exam_query) > 1:
        books = books.filter(subcategory__name__in=exam_query)

    best_seller = Book.objects.filter(category__name='EXAM & STUDY').order_by('?').first()
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

    books = Book.objects.filter(category__name='STORY BOOKS')
    if len(genre_query) == 1:
        books = books.filter(subcategory__name=genre_query[0])
    elif len(genre_query) > 1:
        books = books.filter(subcategory__name__in=genre_query)

    best_seller = Book.objects.filter(category__name='STORY BOOKS').order_by('?').first()
    paginator = Paginator(books, 9)

    page = request.GET.get('page')
    items = paginator.get_page(page)

    return render(request, 'store/story-books.html', {"filter_form":filter_form,"form":form, "items":items, "best_seller":best_seller})
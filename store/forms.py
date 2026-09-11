from django import forms

from store.models import Review

BOOK_DATA=(('all','All Categories'),
           ("title","Title"),
           ("contributor","Contributor"))

class SearchForm(forms.Form):
    search = forms.CharField(min_length=3, required=False, \
                             widget=forms.TextInput(attrs={'class': 'form-control border-0 shadow-none',\
                                                           'placeholder':"Search books, authors and more...",
                                                           'id':'search'}))
    search_in = forms.ChoiceField(choices=BOOK_DATA, required=False,\
                                  widget=forms.Select(attrs={'class': 'form-select border-0 shadow-none pe-5',\
                                                             'id':'categories'}))


class PreSchoolBookFilterForm(forms.Form):
    FILTER_CHOICES = [
        ('KINDERGARTEN I', 'Kindergarten I'),
        ('KINDERGARTEN II', 'Kindergarten II'),
        ('NURSERY I', 'Nursery I'),
        ('NURSERY II', 'Nursery II'),
        ('NURSERY III', 'Nursery III'),
        # Add more filter options as needed
    ]

    filter_option = forms.MultipleChoiceField(
        choices=FILTER_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check'})
    )

class PrimarySchoolBookFilterForm(forms.Form):
    FILTER_CHOICES = [
        ('PRIMARY I', 'Primary I'),
        ('PRIMARY II', 'Primary II'),
        ('PRIMARY III', 'Primary III'),
        ('PRIMARY IV', 'Primary IV'),
        ('PRIMARY V', 'Primary V'),
        ('PRIMARY VI', 'Primary VI'),
        # Add more filter options as needed
    ]

    filter_option = forms.MultipleChoiceField(
        choices=FILTER_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check'})
    )

class HighSchoolBookFilterForm(forms.Form):
    FILTER_CHOICES = [
        ('JUNIOR SECONDARY I', 'JSS I'),
        ('JUNIOR SECONDARY II', 'JSS II'),
        ('JUNIOR SECONDARY III', 'JSS III'),
        ('SENIOR SECONDARY I', 'SSS I'),
        ('SENIOR SECONDARY II', 'SSS II'),
        ('SENIOR SECONDARY III', 'SSS III'),
        # Add more filter options as needed
    ]

    filter_option = forms.MultipleChoiceField(
        choices=FILTER_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check'})
    )

class ExamStudyBookFilterForm(forms.Form):
    FILTER_CHOICES = [
        ('COMMON ENTRANCE PAST QUESTIONS', 'Common Entrance Past Questions'),
        ('JUNIOR WAEC & NECO PAST QUESTIONS AND STUDY GUIDE', 'Junior WAEC & NECO Past Questions And Study Guide'),
        ('SENIOR WAEC & NECO PAST QUESTIONS AND STUDY GUIDE', 'Senior WAEC & NECO PAST QUESTIONS AND STUDY GUIDE'),
        # Add more filter options as needed
    ]

    filter_option = forms.MultipleChoiceField(
        choices=FILTER_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check'})
    )

class StoryBookFilterForm(forms.Form):
    FILTER_CHOICES = [
        ('FICTION', 'Fiction'),
        ('NON-FICTION', 'Non-Fiction'),
        ('ADVENTURE', 'Adventure'),
        ('BEDTIME STORIES', 'Bedtime Stories'),
        ('PICTURE BOOKS', 'Picture Books'),
        # Add more filter options as needed
    ]

    filter_option = forms.MultipleChoiceField(
        choices=FILTER_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check'})
    )


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ("rating",)
        widgets = {
            "rating": forms.RadioSelect(choices=Review.RATINGS),
        }
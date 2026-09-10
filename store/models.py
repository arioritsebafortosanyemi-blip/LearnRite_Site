from django.db import models
from django.contrib import auth

# Create your models here.
class Publisher(models.Model):
    """Name of Publishing Company"""
    name = models.CharField\
        (max_length=50, help_text="The name of the Publisher.")
    website = models.URLField\
        (help_text="The Publisher's website.", blank=True, null=True)
    email = models.EmailField\
        (help_text="The Publisher's email address.", blank=True, null=True)

    def __str__(self):
        return self.name

class Category(models.Model):
    """Categories of Books Published"""
    class BookCategories(models.TextChoices):
        PRE_SCHOOL = "PRE-SCHOOL","Pre-School"
        PRIMARY_SCHOOL = "PRIMARY SCHOOL","Primary School"
        HIGH_SCHOOL = "HIGH SCHOOL","High School"
        EXAM_STUDY = "EXAM & STUDY","Exam & Study"
        STORY_BOOKS = "STORY BOOKS", "Story Books"

    name = models.CharField \
        (help_text="Category the book falls under according to Learnrite",
        choices=BookCategories.choices, max_length=20)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name

class SubCategory(models.Model):
    """Subcategories of Published Books"""
    class SubCategories(models.TextChoices):
        KINDERGARTEN_I = "KINDERGARTEN I","Kindergarten I"
        KINDERGARTEN_II = "KINDERGARTEN II", "Kindergarten II"
        NURSERY_I = "NURSERY I", "Nursery I"
        NURSERY_II = "NURSERY II", "Nursery II"
        NURSERY_III = "NURSERY III", "Nursery III"
        PRIMARY_I = "PRIMARY I", "Primary I"
        PRIMARY_II = "PRIMARY II", "Primary II"
        PRIMARY_III = "PRIMARY III", "Primary III"
        PRIMARY_IV = "PRIMARY IV", "Primary IV"
        PRIMARY_V = "PRIMARY V", "Primary V"
        PRIMARY_VI = "PRIMARY VI", "Primary VI"
        JUNIOR_SECONDARY_I = "JUNIOR SECONDARY I", 'Junior Secondary I'
        JUNIOR_SECONDARY_II = "JUNIOR SECONDARY II", 'Junior Secondary II'
        JUNIOR_SECONDARY_III = "JUNIOR SECONDARY III", 'Junior Secondary III'
        SENIOR_SECONDARY_I = "SENIOR SECONDARY I", 'Senior Secondary I'
        SENIOR_SECONDARY_II = "SENIOR SECONDARY II", 'Senior Secondary II'
        SENIOR_SECONDARY_III = "SENIOR SECONDARY III", 'Senior Secondary III'
        COM_EN_PAST_QUEST = "COMMON ENTRANCE PAST QUESTIONS", 'Common Entrance Past Questions'
        JUNIOR_EXAM_PAST_QUEST = "JUNIOR WAEC & NECO PAST QUESTIONS AND STUDY GUIDE", "Junior WAEC & NECO Past Questions And Study Guide"
        SENIOR_EXAM_PAST_QUEST = "SENIOR WAEC & NECO PAST QUESTIONS AND STUDY GUIDE", "Senior WAEC & NECO Past Questions And Study Guide"
        FICTION = "FICTION", "Fiction"
        NON_FICTION = "NON-FICTION", "Non-Fiction"
        ADVENTURE = "ADVENTURE", "Adventure"
        BEDTIME_STORIES = "BEDTIME STORIES", "Bedtime Stories"
        PICTUREBOOKS = "PICTUREBOOKS", "Picturebooks"

    book_category = models.ForeignKey \
        (Category, on_delete=models.CASCADE)
    name = models.CharField\
        (help_text="Subcategories of Category Field", choices=SubCategories.choices, max_length=50)

    class Meta:
        verbose_name_plural = "Subcategories"

    def __str__(self):
        return self.name

class Contributor(models.Model):
    """A contibutor to a Book, e.g author, editor, co-author."""
    first_names = models.CharField \
        (max_length=50, help_text="The contributor's first name or names.")
    last_names = models.CharField \
        (max_length=50, help_text="The contributor's last name or names. ")
    image = models.ImageField \
        (help_text="Image of the contributor", upload_to="Contributor_Images", default='store/placeholder.png')
    description = models.TextField \
        (help_text="Information about contributor.", max_length=1500, null=True, blank=True)

    def initialled_name(self):
        initials = ' '.join(name for name in self.first_names.split(' '))
        return "{} {}".format(initials, self.last_names)

    def __str__(self):
        return Contributor.initialled_name(self)

class Book(models.Model):
    """Published Book."""
    title = models.CharField \
        (max_length=70, help_text="The title of the book.")
    publication_date = models.DateField \
        (help_text="Date the book was published.")
    book_image = models.ImageField \
        (verbose_name="Cover Image of the book", upload_to="Book_Covers")
    description = models.TextField \
        (verbose_name="Description of the book", max_length=1000)
    publisher = models.ForeignKey \
        (Publisher, related_name="books", on_delete=models.CASCADE)
    category = models.ForeignKey \
        (Category, related_name="books", on_delete=models.CASCADE)
    subcategory = models.ForeignKey \
        (SubCategory, related_name="books", on_delete=models.CASCADE)
    contributors = models.ManyToManyField \
        ("Contributor", through="BookContributor")

    def __str__(self):
        return self.title

class BookPrice(models.Model):
    """One of a book's 4 prices: one per (account type x location) combination."""
    class AccountType(models.TextChoices):
        INDIVIDUAL = "INDIVIDUAL", "Individual"
        SCHOOL = "SCHOOL", "Institution"

    class Location(models.TextChoices):
        LAGOS = "LAGOS", "Lagos"
        OUTSIDE_LAGOS = "OUTSIDE_LAGOS", "Outside Lagos"

    book = models.ForeignKey \
        (Book, related_name="prices", on_delete=models.CASCADE)
    account_type = models.CharField \
        (choices=AccountType.choices, max_length=20)
    location = models.CharField \
        (choices=Location.choices, max_length=20)
    price = models.DecimalField \
        (max_digits=10, decimal_places=2, null=True, blank=True,
         help_text="Leave blank until real pricing is supplied.")

    class Meta:
        unique_together = ("book", "account_type", "location")
        verbose_name_plural = "Book Prices"

    def __str__(self):
        return f"{self.book.title} ({self.account_type}/{self.location})"

class BookContributor(models.Model):
    class ContributionRole(models.TextChoices):
        AUTHOR = "AUTHOR","Author"
        CO_AUTHOR = "CO_AUTHOR","Co-Author"
        EDITOR = "EDITOR","Editor"

    book = models.ForeignKey \
        (Book, on_delete=models.CASCADE)
    contributor = models.ForeignKey \
        (Contributor, on_delete= models.CASCADE)
    role = models.CharField \
        (verbose_name = "The role the contributor had in the book.",
         choices = ContributionRole.choices, max_length=20)

class Review(models.Model):
    RATINGS = (
        (1, '1 star'),
        (2, '2 stars'),
        (3, '3 stars'),
        (4, '4 stars'),
        (5, '5 stars'),
    )

    content = models.TextField \
        (help_text="The review text.")

    rating = models.IntegerField \
        (choices=RATINGS,help_text="The ratings the reviewer has given")

    date_created = models.DateTimeField \
        (auto_now_add=True, help_text="The date and time the review was created")

    date_edited = models.DateTimeField \
        (null=True, help_text="The date and time the review was last edited.")

    creator = models.ForeignKey \
        (auth.get_user_model(), on_delete=models.CASCADE)

    book = models.ForeignKey \
        (Book, on_delete=models.CASCADE, help_text="The book that this review is for.")
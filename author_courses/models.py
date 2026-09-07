from django.db import models


class AuthorCourse(models.Model):
    """Отдельный каталог от Course (см. CLAUDE.md "Открыто" — author.jpg
    показывает свои цены/уровни, career path programs, consulting-блок,
    по объёму это отдельная сущность, не расширение Course)."""

    class Level(models.TextChoices):
        BEGINNER = "beginner", "Beginner"
        INTERMEDIATE = "intermediate", "Intermediate"
        ADVANCED = "advanced", "Advanced"

    class Category(models.TextChoices):
        NAVIGATORS = "navigators", "For Navigators"
        ENGINEERS = "engineers", "For Engineers"

    slug = models.SlugField(unique=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    duration = models.CharField(max_length=255)
    level = models.CharField(max_length=16, choices=Level.choices, default=Level.INTERMEDIATE)
    category = models.CharField(
        max_length=16, choices=Category.choices, default=Category.NAVIGATORS
    )

    price_usd = models.DecimalField(max_digits=10, decimal_places=2)

    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "title"]

    def __str__(self):
        return self.title


class CareerPathProgram(models.Model):
    """"CAREER PATH PROGRAMS FOR NAVIGATORS" секция в author.jpg — отдельные от
    AuthorCourse карточки (Deck Cadet First Step, From 3rd Officer to Chief
    Officer, ...), тот же паттерн category/duration/price."""

    class Category(models.TextChoices):
        NAVIGATORS = "navigators", "For Navigators"
        ENGINEERS = "engineers", "For Engineers"

    slug = models.SlugField(unique=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    duration = models.CharField(max_length=255)
    category = models.CharField(
        max_length=16, choices=Category.choices, default=Category.NAVIGATORS
    )

    price_usd = models.DecimalField(max_digits=10, decimal_places=2)

    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "title"]

    def __str__(self):
        return self.title

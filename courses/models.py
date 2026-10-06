import re

from django.db import models

_HOURS_RE = re.compile(r"^\s*(\d+)\s*hours?\b", re.IGNORECASE)


class TrainingCenter(models.Model):
    """Учебный центр, проводящий обучение. На старте — одна запись (см. CLAUDE.md)."""

    name = models.CharField(max_length=255)
    bank_name = models.CharField(max_length=255)
    bank_country = models.CharField(max_length=255)
    account_number = models.CharField(max_length=64)
    swift = models.CharField(max_length=32)
    currency = models.CharField(max_length=3, default="USD")
    contact_email = models.EmailField()

    # Submerchant receiver_id у Fondy после прохождения KYB (см. CLAUDE.md, шаг 0
    # "До старта платёжного модуля"). Без него Fondy split_rules не собрать.
    fondy_receiver_id = models.CharField(max_length=64, blank=True)

    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Training center"
        verbose_name_plural = "Training centers"

    def __str__(self):
        return self.name


class Course(models.Model):
    class Level(models.TextChoices):
        BEGINNER = "beginner", "Beginner"
        INTERMEDIATE = "intermediate", "Intermediate"
        ADVANCED = "advanced", "Advanced"

    class Category(models.TextChoices):
        NAVIGATORS = "navigators", "For Navigators"
        ENGINEERS = "engineers", "For Engineers"

    class LearningArea(models.TextChoices):
        MARINE_ENGINEERING = "marine_engineering", "Marine Engineering"
        NAVIGATION = "navigation", "Navigation"
        TANKER_OPERATIONS = "tanker_operations", "Tanker Operations"
        SAFETY_COMPLIANCE = "safety_compliance", "Safety & Compliance"
        LEADERSHIP_HUMAN_FACTORS = "leadership_human_factors", "Leadership & Human Factors"

    training_center = models.ForeignKey(
        TrainingCenter, on_delete=models.PROTECT, related_name="courses"
    )

    slug = models.SlugField(unique=True)
    title = models.CharField(max_length=255)
    description = models.TextField()
    requirements = models.TextField(blank=True)

    duration = models.CharField(max_length=255)
    course_dates = models.TextField(blank=True, null=True)

    # Ref-design (course-preview.jpg / online_courses.jpg) shows both a difficulty
    # badge and a "FOR NAVIGATORS/FOR ENGINEERS" category badge per course. Neither
    # was in Course_Description.docx/Course_Prices.docx — filled with best-guess
    # defaults from title/description when the fixture was built (see CLAUDE.md
    # "Каталог курсов"), not authoritative until the customer confirms per course.
    level = models.CharField(
        max_length=16, choices=Level.choices, default=Level.INTERMEDIATE
    )
    category = models.CharField(
        max_length=16, choices=Category.choices, default=Category.NAVIGATORS
    )

    # "Our Maritime Learning Areas" из правок заказчика 2026-10-05 (п.5) — заменили
    # шесть topic-вкладок из online_courses.jpg: home-страница ведёт на каталог,
    # отфильтрованный по направлению (/courses/?area=...). Распределение 53 курсов
    # сделано по предмету курса (миграция 0007), заказчиком per-course не подтверждено.
    learning_area = models.CharField(
        max_length=32, choices=LearningArea.choices, default=LearningArea.SAFETY_COMPLIANCE
    )

    # Правки заказчика п.17: "не требовать документы без необходимости". Seaman's
    # Book и CoC были обязательны для всех курсов, хотя часть аудитории их не имеет
    # (кадеты, рядовой состав, береговой персонал). Настраивается per course в admin.
    requires_seamans_book = models.BooleanField(default=True)
    requires_coc = models.BooleanField(
        default=True, verbose_name="Requires Certificate of Competency"
    )

    # Ref-design shows an instructor card (photo/name/bio) on the course page.
    # No real instructors exist per course yet — generic placeholder text,
    # no photo field (nothing to point it at). Replace with real bios once
    # the customer assigns instructors per course.
    instructor_name = models.CharField(max_length=255, blank=True)
    instructor_bio = models.TextField(blank=True)

    # Nullable: часть курсов в каталоге заказчика ещё не имеет согласованной цены
    # (см. CLAUDE.md "Каталог курсов" — Course_Description vs Course_Prices).
    # Такие курсы остаются видимыми (is_active=True), но чекаут для них недоступен —
    # см. Course.has_price и applications/views.py::apply_form.
    # price_usd — итоговая цена, которую видит и платит кандидат на сайте
    # (заказчик называет её "GMG Academy" — см. CLAUDE.md "Прайсинг"). Она уже
    # включает комиссию партнёра, наценки сверху при оплате нет.
    price_usd = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    price_eur = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    # Доля учебного центра ("MMTC" в прайсинге заказчика) — то, что уходит
    # Meridian Training Center из total_amount при оплате. Разница
    # price_usd − training_center_price_usd — комиссия партнёра (см.
    # CLAUDE.md "Прайсинг" и payments/models.py::get_or_init_for_application).
    # Nullable по той же причине, что и price_usd — часть курсов ещё без
    # согласованной цены.
    training_center_price_usd = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True
    )

    # Ref-design shows a "was $X" struck-through price with a discount badge.
    # Optional — most courses won't have one; set from admin per promotion.
    original_price_usd = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True
    )

    commission_percent = models.DecimalField(max_digits=5, decimal_places=2)

    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title

    @property
    def has_price(self):
        return self.price_usd is not None

    @property
    def duration_hours(self):
        """Number of hours from `duration` ("20 hours"), None for "TBD"/free text."""
        match = _HOURS_RE.match(self.duration or "")
        return int(match.group(1)) if match else None

    @property
    def has_discount(self):
        return (
            self.has_price
            and self.original_price_usd is not None
            and self.original_price_usd > self.price_usd
        )

    @property
    def discount_percent(self):
        if not self.has_discount:
            return None
        return round((1 - self.price_usd / self.original_price_usd) * 100)

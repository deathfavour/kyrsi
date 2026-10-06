"""Static export of the site for the GitHub Pages design preview
(https://deathfavour.github.io/kyrsi/).

    python manage.py build_static_preview --out gh-pages-build --base-path /kyrsi/

Renders every public page through the Django test client against the current DB
(load courses/author_courses fixtures first), rewrites root-relative links for the
Pages sub-path and copies static/img. The checkout is exported step by step for
every priced course; the Application/Payment objects needed for that are created
inside a transaction that is rolled back. Forms cannot submit on static hosting:
checkout forms navigate to the next exported step, all other forms show a notice.
"""

import re
import shutil
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from applications.models import Application
from author_courses.models import AuthorCourse
from courses.models import Course
from payments.models import Payment

STATIC_PAGES = [
    "courses:home",
    "courses:course_list",
    "author_courses:author_course_list",
    "pages:our_services",
    "pages:about_us",
    "pages:contact_us",
    "pages:photo_credits",
    "legal:terms",
    "legal:privacy_policy",
    "legal:refund_policy",
    "refunds:request_refund",
    "support:ask_question",
]

PREVIEW_SCRIPT = """
<div id="preview-toast" style="display:none"
     class="fixed bottom-24 left-1/2 -translate-x-1/2 z-50 bg-blue-950 text-white text-sm
            rounded-lg shadow-lg px-4 py-3 max-w-xs text-center">
  Design preview: forms are not connected on this static site.
</div>
<script>
document.addEventListener('submit', function (e) {
  e.preventDefault();
  e.stopPropagation();
  var next = e.target.getAttribute('data-preview-next');
  if (next) { window.location.href = next; return; }
  var toast = document.getElementById('preview-toast');
  toast.style.display = 'block';
  clearTimeout(window.__previewToast);
  window.__previewToast = setTimeout(function () { toast.style.display = 'none'; }, 3500);
}, true);
</script>
"""

_HTMX_SCRIPT_RE = re.compile(r'<script src="https://unpkg\.com/htmx\.org[^"]*"></script>\s*')
_HX_ATTR_RE = re.compile(r'\shx-[a-z-]+="[^"]*"')
_ROOT_URL_RE = re.compile(r'(\s(?:href|src|action))="/(?!/)')


class Command(BaseCommand):
    help = "Export the public site as static HTML for the GitHub Pages preview."

    def add_arguments(self, parser):
        parser.add_argument("--out", default="gh-pages-build")
        parser.add_argument("--base-path", default="/kyrsi/")

    def handle(self, *args, out, base_path, **options):
        self.out = Path(out).resolve()
        self.base = "/" + base_path.strip("/") + "/"
        self.client = Client(HTTP_HOST="localhost")
        # Empty the folder instead of deleting it: OneDrive/Windows can hold a
        # lock on the directory itself.
        self.out.mkdir(parents=True, exist_ok=True)
        for child in self.out.iterdir():
            if child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink()

        count = 0
        for name in STATIC_PAGES:
            count += self._export(reverse(name))
        for course in Course.objects.filter(is_active=True):
            count += self._export(reverse("courses:course_detail", args=[course.slug]))
        for author_course in AuthorCourse.objects.filter(is_active=True):
            count += self._export(
                reverse("author_courses:author_course_detail", args=[author_course.slug])
            )
        count += self._export_checkout()

        shutil.copytree(Path(settings.BASE_DIR) / "static" / "img", self.out / "static" / "img")
        (self.out / ".nojekyll").write_text("", encoding="utf-8")
        self.stdout.write(self.style.SUCCESS(f"Exported {count} pages to {self.out}"))

    def _export_checkout(self):
        """Form -> confirm -> payment -> success for every priced course, exported to
        stable paths apply/<slug>/{,confirm/,payment/,success/}."""
        count = 0
        with transaction.atomic():
            for course in Course.objects.filter(is_active=True, price_usd__isnull=False):
                application = Application.objects.create(
                    course=course,
                    full_name="Preview Candidate",
                    date_of_birth="1990-01-01",
                    citizenship="Georgia",
                    position="Officer",
                    phone="+995000000000",
                    email="preview@example.com",
                    agreed_terms_at=timezone.now(),
                )
                payment, _ = Payment.objects.get_or_init_for_application(application)
                steps = {
                    "form": (reverse("applications:apply_form", args=[course.slug]), ""),
                    "confirm": (
                        reverse("applications:apply_confirm", args=[course.slug, application.pk]),
                        "confirm/",
                    ),
                    "payment": (
                        reverse("applications:apply_payment", args=[course.slug, application.pk]),
                        "payment/",
                    ),
                }
                course_root = reverse("applications:apply_form", args=[course.slug])
                next_step = {
                    steps["form"][0]: "confirm/",
                    steps["confirm"][0]: "payment/",
                    reverse("payments:initiate", args=[course.slug, application.pk]): "success/",
                }
                for url, suffix in steps.values():
                    count += self._export(url, target=course_root + suffix, next_step=next_step,
                                          course_root=course_root)
                payment.status = Payment.Status.PAID
                payment.paid_at = timezone.now()
                payment.save(update_fields=["status", "paid_at"])
                count += self._export(
                    reverse("payments:success", args=[course.slug, application.pk]),
                    target=course_root + "success/",
                )
            transaction.set_rollback(True)
        return count

    def _export(self, url, target=None, next_step=None, course_root=None):
        response = self.client.get(url)
        if response.status_code != 200:
            raise RuntimeError(f"{url} returned {response.status_code}")
        html = response.content.decode()
        if next_step:
            html = self._wire_checkout_forms(html, next_step, course_root)
        html = _HTMX_SCRIPT_RE.sub("", html)
        html = _HX_ATTR_RE.sub("", html)
        html = _ROOT_URL_RE.sub(lambda m: f'{m.group(1)}="{self.base}', html)
        html = html.replace("</body>", PREVIEW_SCRIPT + "</body>", 1)

        path = self.out / (target or url).strip("/") / "index.html"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(html, encoding="utf-8")
        return 1

    def _wire_checkout_forms(self, html, next_step, course_root):
        def wire(match):
            tag = match.group(0)
            target = re.search(r'(?:hx-post|action)="([^"]+)"', tag)
            if not target or target.group(1) not in next_step:
                return tag
            href = self.base + (course_root + next_step[target.group(1)]).lstrip("/")
            return tag.replace("<form", f'<form novalidate data-preview-next="{href}"', 1)

        return re.sub(r"<form\b[^>]*>", wire, html)

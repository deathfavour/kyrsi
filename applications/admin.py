from django.contrib import admin

from config.excel_export import export_queryset_to_xlsx

from .models import Application, ApplicationDocument


class ApplicationDocumentInline(admin.TabularInline):
    model = ApplicationDocument
    extra = 0
    readonly_fields = ("uploaded_at",)


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ("full_name", "course", "email", "phone", "agreed_terms_at", "created_at")
    list_filter = ("course", "citizenship")
    search_fields = ("full_name", "email", "phone")
    readonly_fields = ("agreed_terms_at", "created_at")
    date_hierarchy = "created_at"
    inlines = [ApplicationDocumentInline]
    actions = ["export_to_excel"]

    @admin.action(description="Export selected applications to Excel")
    def export_to_excel(self, request, queryset):
        columns = [
            ("Full Name", lambda a: a.full_name),
            ("Course", lambda a: a.course.title),
            ("Date of Birth", lambda a: a.date_of_birth),
            ("Citizenship", lambda a: a.citizenship),
            ("Position", lambda a: a.position),
            ("Company", lambda a: a.company or ""),
            ("Phone", lambda a: a.phone),
            ("Email", lambda a: a.email),
            ("Agreed Terms At", lambda a: a.agreed_terms_at),
            ("Created At", lambda a: a.created_at),
        ]
        return export_queryset_to_xlsx(queryset, columns, "applications.xlsx")

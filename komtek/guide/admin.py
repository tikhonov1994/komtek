from django.contrib import admin

from guide.models import Guide, GuideElement


@admin.register(Guide)
class GuideAdmin(admin.ModelAdmin):
    pass


@admin.register(GuideElement)
class GuideElementAdmin(admin.ModelAdmin):
    pass

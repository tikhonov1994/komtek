import django_filters

from guide.models import Guide, GuideElement


class GuideFilter(django_filters.FilterSet):
    # MySQL не поддерживает операторы с учетом регистра
    name = django_filters.CharFilter(lookup_expr='contains')
    start_date = django_filters.DateFilter(lookup_expr='gte', label='От даты')

    class Meta:
        model = Guide
        fields = []


class GuideElementFilter(django_filters.FilterSet):
    # MySQL не поддерживает операторы с учетом регистра
    element_code = django_filters.CharFilter(lookup_expr='contains')
    value = django_filters.CharFilter(lookup_expr='contains')

    class Meta:
        model = GuideElement
        fields = []

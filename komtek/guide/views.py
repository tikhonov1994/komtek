import datetime as dt

from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator
from django.shortcuts import redirect
from django.views.generic import FormView, ListView
from rest_framework import generics, status
from rest_framework.response import Response

from guide.filters import GuideElementFilter, GuideFilter
from guide.forms import GuideElementEnterForm, GuideEnterForm
from guide.models import Guide, GuideElement
from guide.serializers import GuideElementSerializer, GuideSerializer


class GuideList(generics.GenericAPIView):
    """
    Получение списка справочников.
    """
    serializer_class = GuideSerializer

    def get_queryset(self, **kwargs):
        return Guide.objects.filter(**kwargs).order_by('id')

    def get(self, request):
        """
        На GET запрос присылает список всех справочников.
        """
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def post(self, request):
        """
        На POST запрос присылает список всех справочников, актуальных на дату
        в параметре "date":"YYYY-MM-DD"
        При POST запросе с пустым параметром "date" вернет все актуальные
        на сегодня справочники
        """
        date = request.data.get('date', None)
        if date is None:
            date = dt.date.today()
        queryset = self.get_queryset(start_date__lte=date)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class GuideElementsList(generics.GenericAPIView):
    """
    Получение элементов заданного справочника.
    """
    serializer_class = GuideElementSerializer

    def get_queryset(self):
        version = self.request.query_params.get('version', None)
        if version is not None:
            queryset = GuideElement.objects.filter(guide__version=version)
        else:
            actual_guide = Guide.objects.filter(
                start_date__lte=dt.date.today()
            ).order_by('start_date').last()
            queryset = GuideElement.objects.filter(guide=actual_guide)
        return queryset.order_by('id')

    def get(self, request):
        """
        На GET запрос без параметров присылает все элементы справочника
        актуальной версии
        На GET запрос с url-параметром ?version=<version> присылает все
        элементы справочника указанной версии
        """
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def post(self, request):
        """
        На POST запрос проверяет валидность элементов справочника
        актуальной версии или версии из url-параметра version
        Элементы можно отправить в виде списка:
        [{"element_code":"Код элемента",
          "value":"Значение элемента"},...]
        Либо по одному:
        {"element_code":"Код элемента",
         "value":"Значение элемента"}
        """
        result_data = {}
        if isinstance(request.data, list):
            index = 0
            for elem in request.data:
                if (
                    elem.get('element_code') is not None and
                    elem.get('value') is not None
                ):
                    result_data = result_data | {
                        index: self.get_queryset().filter(
                            element_code=elem.get('element_code'),
                            value=elem.get('value')
                        ).exists()}
                    index += 1
                else:
                    result_data = result_data | {index: False}
                    index += 1
        else:
            result_data = {0: self.get_queryset().filter(
                element_code=request.data.get('element_code'),
                value=request.data.get('value')
            ).exists()}
        return Response(result_data, status=status.HTTP_200_OK)


class GuideListView(ListView):
    model = Guide
    filterset_class = GuideFilter
    queryset = Guide.objects.order_by('pk')
    template_name = 'guide_table.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        guides = self.get_queryset()
        paginator = Paginator(guides, 10)
        page_number = self.request.GET.get('page', 1)
        page = paginator.get_page(page_number)
        page_range = paginator.get_elided_page_range(number=page_number)
        context['page'] = page
        context['page_range'] = page_range
        context['paginator'] = paginator
        context['filter'] = self.filter
        return context

    def get_queryset(self):
        qs = super().get_queryset()
        self.filter = self.filterset_class(self.request.GET, queryset=qs)
        return self.filter.qs


class EnterGuideView(FormView):
    """
    Класс ответчает за добавление или обновление списка справочников
    При попытке создания справочника с той же версией, справочник обновится.
    """
    template_name = 'form.html'
    form_class = GuideEnterForm

    def form_valid(self, form):
        guide, _ = Guide.objects.update_or_create(
            version=form.cleaned_data.get('version'),
            defaults={
                'name': form.cleaned_data.get('name'),
                'short_name': form.cleaned_data.get('short_name'),
                'description': form.cleaned_data.get('description'),
                'start_date': form.cleaned_data.get('start_date'),
            }
        )
        guide.save()
        return redirect('guide:guide_table')


class GuideElementsListView(ListView):
    model = GuideElement
    filterset_class = GuideElementFilter
    queryset = GuideElement.objects.order_by('pk')
    template_name = 'guide_element_table.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        guides = self.get_queryset()
        paginator = Paginator(guides, 10)
        page_number = self.request.GET.get('page', 1)
        page = paginator.get_page(page_number)
        page_range = paginator.get_elided_page_range(number=page_number)
        context['page'] = page
        context['page_range'] = page_range
        context['paginator'] = paginator
        context['filter'] = self.filter
        context['guide_pk'] = self.kwargs.get('guide_pk')
        return context

    def get_queryset(self):
        qs = self.queryset.filter(guide__pk=self.kwargs.get('guide_pk'))
        self.filter = self.filterset_class(self.request.GET, queryset=qs)
        return self.filter.qs


class EnterGuideElementView(FormView):
    """
    Класс ответчает за добавление или обновление списка элементов справочников
    При попытке создания элемента с уже имеющимся кодом, значение обновится.
    """
    template_name = 'form.html'
    form_class = GuideElementEnterForm

    def form_valid(self, form):
        try:
            element, _ = GuideElement.objects.update_or_create(
                guide=Guide.objects.get(pk=self.kwargs.get('guide_pk')),
                element_code=form.cleaned_data.get('element_code'),
                defaults={
                    'value': form.cleaned_data.get('value'),
                }
            )
            element.save()
            return redirect('guide:guide_elements_table',
                            self.kwargs.get('guide_pk'))
        except ObjectDoesNotExist:
            form.add_error(field=None,
                           error=('Не найден справочник с id '
                                  f'{self.kwargs.get("guide_pk")}'))
            return self.form_invalid(form)

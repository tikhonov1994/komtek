import datetime as dt

from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.paginator import Paginator
from django.shortcuts import redirect
from django.views.generic import FormView, ListView
from rest_framework import generics, status
from rest_framework.response import Response

from guide.exceptions import UrlParamMissing
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
        На GET запрос без параметров присылает список всех справочников.
        На GET запрос с url-параметром ?date=actual присылает все
        актуальные на сегодня справочники
        На GET запрос с url-параметром ?date=YYYY-MM-DD присылает
        список всех справочников, актуальных на дату "YYYY-MM-DD"
        """
        date = self.request.query_params.get('date', None)
        if date is None:
            queryset = self.get_queryset()
        else:
            if date == 'actual':
                date = dt.date.today()
            try:
                elems_pk = []
                # Получаем список уникальных наименований справочников
                names_unique = Guide.objects.values_list('name').distinct()
                for name in names_unique:
                    # Получаем по одному актуальные справочники по
                    # наименованию и дате начала действия
                    elem = Guide.objects.filter(
                        name=name[0], start_date__lte=date
                    ).latest('start_date')
                    # Записываем ID полученных справочников
                    elems_pk.append(elem.pk)
                queryset = self.get_queryset(pk__in=elems_pk)
            except ValidationError as e:
                return Response({"error": e},
                                status=status.HTTP_400_BAD_REQUEST)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            serializer.is_valid(raise_exception=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class GuideElementsList(generics.GenericAPIView):
    """
    Получение элементов заданного справочника.
    """
    serializer_class = GuideElementSerializer

    def get_queryset(self):
        guide_name = self.request.query_params.get('name', None)
        if guide_name is None:
            raise UrlParamMissing
        version = self.request.query_params.get('version', None)
        if version is not None:
            queryset = GuideElement.objects.filter(
                guide__version=version, guide__name=guide_name)
        else:
            actual_guide = Guide.objects.filter(
                start_date__lte=dt.date.today(),
                name=guide_name
            ).latest('start_date')
            queryset = GuideElement.objects.filter(guide=actual_guide)
        return queryset.order_by('id')

    def get(self, request):
        """
        На GET запрос с url-параметром ?name=<Имя справочника> присылает все
        элементы справочника "Имя справочника" актуальной версии
        На GET запрос с параметрами ?name=<Имя справочника>&version=<version>
        присылает все элементы справочника указанной версии
        """
        try:
            queryset = self.get_queryset()
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
        except UrlParamMissing:
            return Response({"error": "Не указан url-параметр name"},
                            status=status.HTTP_400_BAD_REQUEST)

    def post(self, request):
        """
        На POST запрос проверяет валидность элементов справочника из
        url-параметра name актуальной версии или версии из параметра version
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
            name=form.cleaned_data.get('name'),
            defaults={
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

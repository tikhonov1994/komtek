from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django import forms


class GuideEnterForm(forms.Form):
    name = forms.CharField(max_length=255, label='Наименование',
                           required=False)
    short_name = forms.CharField(max_length=63, label='Короткое наименование',
                                 required=False)
    description = forms.CharField(label='Описание', widget=forms.Textarea,
                                  required=False)
    version = forms.CharField(max_length=63, label='Версия')
    start_date = forms.DateField(
        label='Дата начала действия справочника этой версии')

    helper = FormHelper()
    helper.form_method = 'POST'
    helper.add_input(Submit('submit', 'Добавить справочник',
                     css_class='btn btn-block btn-primary'))


class GuideElementEnterForm(forms.Form):
    element_code = forms.CharField(max_length=255, label='Код элемента')
    value = forms.CharField(max_length=63, label='Значение')

    helper = FormHelper()
    helper.form_method = 'POST'
    helper.add_input(Submit('submit', 'Добавить элемент справочника',
                     css_class='btn btn-block btn-primary'))

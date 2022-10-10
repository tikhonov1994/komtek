from django.urls import path

from guide.views import (EnterGuideElementView, EnterGuideView,
                         GuideElementsList, GuideElementsListView, GuideList,
                         GuideListView)

app_name = 'guide'

urlpatterns = [
    path('api/get-guides', GuideList.as_view()),
    path('api/get-elements', GuideElementsList.as_view()),
    path('', GuideListView.as_view(), name='guide_table'),
    path('enter-guide', EnterGuideView.as_view(), name='enter_guide'),
    path('guide-elements/<int:guide_pk>',
         GuideElementsListView.as_view(), name='guide_elements_table'),
    path('guide-elements/<int:guide_pk>/enter',
         EnterGuideElementView.as_view(), name='enter_guide_element'),
]

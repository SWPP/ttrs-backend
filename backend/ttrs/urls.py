from django.urls import path

from . import views

urlpatterns = [
    path('test/', views.test),

    # TODO: implements views for these urls
    #     path('students/'),
    #     path('students/signin/'),
    #     path('students/signup/'),
    #     path('students/validate/'),
    #     path('students/withdraw/'),
    #     path('students/not-recommend/'),
    #
    #     path('timetables/<str:type>/'),
    #     path('timetables/recommend/'),
    #     path('timetables/send/<str:student>'),
    #
    #     path('lectures'),
    #
    #     path('majors'),
    #
    #     path('evaluations/lecture/<int:lecture_id>'),
    #     path('evaluations/<int:evaluations_id>'),
]

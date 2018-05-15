from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns

from . import views

urlpatterns = [
    path('students/', views.StudentList.as_view()),
    path('students/signup/', views.StudentCreate.as_view()),
    path('students/my/', views.StudentDetail.as_view()),

    path('courses/', views.CourseList.as_view()),
    path('courses/<int:pk>/', views.CourseDetail.as_view()),
    path('lectures/', views.LectureList.as_view()),
    path('lectures/<int:pk>/', views.LectureDetail.as_view()),

    path('evaluations/', views.EvaluationList.as_view()),
    path('evaluations/<int:pk>/', views.EvaluationDetail.as_view()),
    path('evaluations/<int:pk>/likeit/', views.EvaluationLikeIt.as_view()),

    path('my-time-tables/', views.MyTimeTableList.as_view()),
    path('my-time-tables/<int:pk>/', views.MyTimeTableDetail.as_view()),
    path('bookmarked-time-tables/', views.BookmarkedTimeTableList.as_view()),
    path('bookmarked-time-tables/<int:pk>/', views.BookmarkedTimeTableDetail.as_view()),
    path('received-time-tables/', views.ReceivedTimeTableList.as_view()),
    path('received-time-tables/<int:pk>/', views.ReceivedTimeTableDetail.as_view()),
    path('received-time-tables/<int:pk>/receive', views.ReceiveTimeTable.as_view()),
    path('time-tables/copy-to-my/', views.CopyToMyTimeTable.as_view()),
    path('time-tables/bookmark/', views.BookmarkTimeTable.as_view()),
    path('time-tables/send/', views.SendTimeTable.as_view()),

    path('colleges/', views.CollegeList.as_view()),
    path('departments/', views.DepartmentList.as_view()),
    path('majors/', views.MajorList.as_view()),

    path('recommends/', views.RecommendView.as_view()),
]

urlpatterns += format_suffix_patterns(urlpatterns)

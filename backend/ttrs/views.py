from django.core.exceptions import FieldError, ObjectDoesNotExist
from django.utils import timezone
from rest_framework import generics
from rest_framework.exceptions import ParseError
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.response import Response
from rest_framework.status import HTTP_201_CREATED

from .permissions import IsStudentOrReadOnly, IsOtherStudent, IsStudent, IsTheStudent
from .serializers import StudentSerializer, CollegeSerializer, DepartmentSerializer, MajorSerializer, \
    CourseSerializer, LectureSerializer, EvaluationSerializer, EvaluationDetailSerializer, MyTimeTableSerializer, \
    BookmarkedTimeTableSerializer, ReceivedTimeTableSerializer, SendTimeTableSerializer, CopyTimeTableSerializer, \
    TimeTableSerializer
from .models import Student, College, Department, Major, Course, Lecture, Evaluation, MyTimeTable, BookmarkedTimeTable, \
    ReceivedTimeTable, TimeTable

from .recommend import recommend


class FilterAPIView(generics.GenericAPIView):
    """
    Custom supporting APIView for filtering queryset based on query_params.

    By extending this class, the APIView will automatically filter queryset if the request
    has query_params.
    Keys of the query_params MUST be a valid key of the function 'QuerySet.filter', or
    raises ParseError with status 400.
    """

    def filter_queryset(self, queryset):
        errors = {}
        for key, value in self.request.query_params.items():
            try:
                queryset.filter(**{key: value})
            except (FieldError, ValueError) as e:
                error_key = '{}={}'.format(key, value)
                error_value = list(e.args)
                errors[error_key] = error_value
        if errors:
            raise ParseError(errors)
        return queryset.filter(**self.request.query_params.dict())


class StudentList(generics.ListAPIView):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    permission_classes = (IsAdminUser,)


class StudentCreate(generics.CreateAPIView):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    permission_classes = (AllowAny,)


class StudentDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    permission_classes = (IsAuthenticated, IsStudent)

    def get_object(self):
        return Student.objects.get_by_natural_key(self.request.user.username)


class CourseList(FilterAPIView, generics.ListAPIView):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = (IsAuthenticated,)


class CourseDetail(generics.RetrieveAPIView):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = (IsAuthenticated,)


class LectureList(FilterAPIView, generics.ListAPIView):
    queryset = Lecture.objects.all()
    serializer_class = LectureSerializer
    permission_classes = (IsAuthenticated,)


class LectureDetail(generics.RetrieveAPIView):
    queryset = Lecture.objects.all()
    serializer_class = LectureSerializer
    permission_classes = (IsAuthenticated,)


class EvaluationList(FilterAPIView, generics.ListCreateAPIView):
    queryset = Evaluation.objects.all()
    serializer_class = EvaluationSerializer
    permission_classes = (IsAuthenticated, IsStudentOrReadOnly)

    def perform_create(self, serializer):
        serializer.save(author=Student.objects.get_by_natural_key(self.request.user.username))


class EvaluationDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Evaluation.objects.all()
    serializer_class = EvaluationDetailSerializer
    permission_classes = (IsAuthenticated, IsTheStudent)


class EvaluationLikeIt(generics.RetrieveDestroyAPIView):
    queryset = Evaluation.objects.all()
    serializer_class = EvaluationDetailSerializer
    permission_classes = (IsAuthenticated, IsOtherStudent)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.like_it.add(Student.objects.get_by_natural_key(request.user.username))
        instance.save()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.like_it.remove(Student.objects.get_by_natural_key(request.user.username))
        instance.save()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class MyTimeTableList(FilterAPIView, generics.ListCreateAPIView):
    """
    If the student have a TimeTable with given year and semester already,
    the existing TimeTable will be overwritten by new TimeTable.
    """
    serializer_class = MyTimeTableSerializer
    permission_classes = (IsAuthenticated, IsStudent)

    def get_queryset(self):
        return MyTimeTable.objects.filter(owner__username=self.request.user.username)

    def perform_create(self, serializer):
        owner = Student.objects.get_by_natural_key(self.request.user.username)
        try:
            old_time_table = MyTimeTable.objects.get(year=serializer.year, semester=serializer.semester, owner=owner)
            old_time_table.delete()
        except ObjectDoesNotExist:
            pass
        serializer.save(owner=owner)


class MyTimeTableDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = MyTimeTableSerializer
    permission_classes = (IsAuthenticated, IsStudent)

    def get_queryset(self):
        return MyTimeTable.objects.filter(owner__username=self.request.user.username)


class BookmarkedTimeTableList(FilterAPIView, generics.ListCreateAPIView):
    serializer_class = BookmarkedTimeTableSerializer
    permission_classes = (IsAuthenticated, IsStudent)

    def get_queryset(self):
        return BookmarkedTimeTable.objects.filter(owner__username=self.request.user.username)

    def perform_create(self, serializer):
        serializer.save(owner=Student.objects.get_by_natural_key(self.request.user.username))


class BookmarkedTimeTableDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = BookmarkedTimeTableSerializer
    permission_classes = (IsAuthenticated, IsStudent)

    def get_queryset(self):
        return BookmarkedTimeTable.objects.filter(owner__username=self.request.user.username)


class ReceivedTimeTableList(FilterAPIView, generics.ListAPIView):
    serializer_class = ReceivedTimeTableSerializer
    permission_classes = (IsAuthenticated, IsStudent)

    def get_queryset(self):
        return ReceivedTimeTable.objects.filter(owner__username=self.request.user.username)


class ReceivedTimeTableDetail(generics.RetrieveDestroyAPIView):
    serializer_class = ReceivedTimeTableSerializer
    permission_classes = (IsAuthenticated, IsStudent)

    def get_queryset(self):
        return ReceivedTimeTable.objects.filter(owner__username=self.request.user.username)


class ReceiveTimeTable(generics.RetrieveAPIView):
    """
    Perform receiving the TimeTable.
    """
    serializer_class = ReceivedTimeTableSerializer
    permission_classes = (IsAuthenticated, IsStudent)

    def get_queryset(self):
        return ReceivedTimeTable.objects.filter(owner__username=self.request.user.username)

    def retrieve(self, request, *args, **kwargs):
        time_table = self.get_object()
        if time_table.received_at is None:
            time_table.received_at = timezone.now()
            time_table.save()
        serializer = self.get_serializer(time_table)
        return Response(serializer.data)


class CopyTimeTable(generics.CreateAPIView):
    """
    Base APIView for copying or overwriting TimeTable.
    """
    permission_classes = (IsAuthenticated, IsStudent)
    serializer_class = CopyTimeTableSerializer

    def get_serializer(self, *args, **kwargs):
        serializer_class = self.get_serializer_class()
        kwargs['context'] = self.get_serializer_context()
        return serializer_class(*args, **kwargs, owner=Student.objects.get_by_natural_key(self.request.user.username))

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_time_table_id = self.perform_create(serializer)
        return Response({"created_time_table": new_time_table_id}, status=HTTP_201_CREATED)


class CopyToMyTimeTable(CopyTimeTable):
    def perform_create(self, serializer):
        time_table = TimeTable.objects.get(pk=serializer.data['time_table_id'])
        owner = Student.objects.get_by_natural_key(serializer.owner)
        try:
            old_time_table = MyTimeTable.objects.get(year=time_table.year, semester=time_table.semester, owner=owner)
            old_time_table.delete()
        except ObjectDoesNotExist:
            pass
        new_time_table = MyTimeTable(other=time_table, owner=owner)
        new_time_table.save_m2m()
        return new_time_table.id


class BookmarkTimeTable(CopyTimeTable):
    def perform_create(self, serializer):
        time_table = TimeTable.objects.get(pk=serializer.data['time_table_id'])
        owner = Student.objects.get_by_natural_key(serializer.owner)
        new_time_table = BookmarkedTimeTable(other=time_table, owner=owner)
        new_time_table.save_m2m()
        return new_time_table.id


class SendTimeTable(CopyTimeTable):
    serializer_class = SendTimeTableSerializer

    def perform_create(self, serializer):
        time_table = TimeTable.objects.get(pk=serializer.data['time_table_id'])
        owner = Student.objects.get_by_natural_key(serializer.data['receiver_name'])
        sender = Student.objects.get_by_natural_key(serializer.owner)
        new_time_table = ReceivedTimeTable(other=time_table, owner=owner, sender=sender)
        new_time_table.save_m2m()
        return new_time_table.id


class CollegeList(FilterAPIView, generics.ListAPIView):
    queryset = College.objects.all()
    serializer_class = CollegeSerializer
    permission_classes = (AllowAny,)


class DepartmentList(FilterAPIView, generics.ListAPIView):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = (AllowAny,)


class MajorList(FilterAPIView, generics.ListAPIView):
    queryset = Major.objects.all()
    serializer_class = MajorSerializer
    permission_classes = (AllowAny,)


class RecommendView(generics.ListAPIView):
    serializer_class = TimeTableSerializer
    permission_classes = (IsAuthenticated, IsStudent)

    def get_queryset(self):
        options = self.request.query_params.copy()
        student = Student.objects.get_by_natural_key(self.request.user.username)
        return recommend(options, student)

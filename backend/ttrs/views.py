from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import FieldError, ObjectDoesNotExist
from django.core.mail import EmailMessage
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.utils import timezone
from django.conf import settings
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from rest_framework import generics
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.response import Response
from rest_framework.status import HTTP_201_CREATED

from .tokens import account_activation_token
from .permissions import IsStudentOrReadOnly, IsOtherStudent, IsStudent, IsTheStudentOrReadOnly
from .serializers import StudentSerializer, CollegeSerializer, DepartmentSerializer, MajorSerializer, \
    CourseSerializer, LectureSerializer, EvaluationSerializer, EvaluationDetailSerializer, MyTimeTableSerializer, \
    BookmarkedTimeTableSerializer, ReceivedTimeTableSerializer, SendTimeTableSerializer, CopyTimeTableSerializer, \
    RecommendedTimeTableSerializer, SemesterSerializer
from .models import Student, College, Department, Major, Course, Lecture, Evaluation, MyTimeTable, BookmarkedTimeTable, \
    ReceivedTimeTable, TimeTable

from .recommend2 import recommend, contains, load


class FilterOrderAPIView(generics.GenericAPIView):
    """
    Custom supporting APIView for filtering and ordering queryset based on query_params.

    By extending this class, the APIView will automatically filter and order queryset
    if the request has query_params.
    Keys of the query_params that is not valid for the function 'QuerySet.filter', except 'order_by', would be ignored.
    The value of the key 'order_by' that is not valid for the function 'QuerySet.order_by' would be ignored.
    """

    def filter_queryset(self, queryset):
        ordering = None
        options = {}
        for key, value in self.request.query_params.items():
            if key == 'order_by' and value:
                try:
                    queryset.filter(**{value[value[0]=='-':]+'__isnull': 'True'})
                    ordering = value
                except (FieldError, ValueError) as e:
                    print(e)
                    pass
                continue
            try:
                queryset.filter(**{key: value})
                options.update({key: value})
            except (FieldError, ValueError):
                pass
        if ordering:
            return queryset.filter(**options).order_by(ordering)
        return queryset.filter(**options)


class StudentList(generics.ListAPIView):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    permission_classes = (IsAdminUser,)


class StudentCreate(generics.CreateAPIView):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    permission_classes = (AllowAny,)

    def perform_create(self, serializer):
        student = serializer.save()
        #student = serializer.save(is_active=False) Just commented out for development environment
        current_site = get_current_site(self.request)
        mail_subject = 'Activate your account.'
        message = render_to_string('acc_active_email.html', {
            'user': student,
            'domain': current_site.domain,
            'uid': urlsafe_base64_encode(force_bytes(student.pk)).decode(),
            'token': account_activation_token.make_token(student),
        })
        to_email = student.email
        email = EmailMessage(mail_subject, message, to=[to_email])
        email.send()


def activate(request, uidb64, token):
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = Student.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, Student.DoesNotExist):
        user = None
    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        return HttpResponse('Thank you for your email confirmation. Now you can login your account.')
    else:
        return HttpResponse('Activation link is invalid!')


class StudentDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    permission_classes = (IsAuthenticated, IsStudent)

    def get_object(self):
        return Student.objects.get_by_natural_key(self.request.user.username)


class CourseList(FilterOrderAPIView, generics.ListAPIView):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = LimitOffsetPagination


class CourseDetail(generics.RetrieveAPIView):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = (IsAuthenticated,)


class LectureList(FilterOrderAPIView, generics.ListAPIView):
    queryset = Lecture.objects.all()
    serializer_class = LectureSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = LimitOffsetPagination

    def filter_queryset(self, queryset):
        if 'blocks' in self.request.query_params:
            blocks = self.request.query_params.get('blocks')
            blocks = [[list(map(int, slot.split(':'))) for slot in slots.split(',')] if slots else [] for slots in blocks.split('|')]
            whole_lectures, ignore = load(int(self.request.query_params.get('year')), self.request.query_params.get('semester'))
            lectures = []
            for lecture in whole_lectures:
                if contains(blocks, lecture.time_slot_set):
                    lectures.append(lecture.id)
            queryset = Lecture.objects.filter(pk__in=lectures)
        return FilterOrderAPIView.filter_queryset(self, queryset)


class LectureDetail(generics.RetrieveAPIView):
    queryset = Lecture.objects.all()
    serializer_class = LectureSerializer
    permission_classes = (IsAuthenticated,)


class EvaluationList(FilterOrderAPIView, generics.ListCreateAPIView):
    queryset = Evaluation.objects.all()
    serializer_class = EvaluationSerializer
    permission_classes = (IsAuthenticated, IsStudentOrReadOnly)

    def perform_create(self, serializer):
        serializer.save(author=Student.objects.get_by_natural_key(self.request.user.username))


class EvaluationDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Evaluation.objects.all()
    serializer_class = EvaluationDetailSerializer
    permission_classes = (IsAuthenticated, IsStudent, IsTheStudentOrReadOnly)


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


class MyTimeTableList(FilterOrderAPIView, generics.ListCreateAPIView):
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


class BookmarkedTimeTableList(FilterOrderAPIView, generics.ListCreateAPIView):
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


class ReceivedTimeTableList(FilterOrderAPIView, generics.ListAPIView):
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
    Perform receiving(reading) the TimeTable.
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


class SemesterList(generics.ListAPIView):
    serializer_class = SemesterSerializer
    permission_classes = (AllowAny,)

    def get_queryset(self):
        years = {}
        for lecture in Lecture.objects.all():
            if lecture.year not in years:
                years[lecture.year] = [None]*4
            for i, semester in enumerate(settings.SEMESTER_CHOICES):
                if semester[0] == lecture.semester:
                    years[lecture.year][3-i] = lecture.semester
        years_semesters = []
        for year in sorted(years, reverse=True):
            for semester in years[year]:
                if semester:
                    years_semesters.append(dict(year=year, semester=semester))
        return years_semesters


class CollegeList(FilterOrderAPIView, generics.ListAPIView):
    queryset = College.objects.all()
    serializer_class = CollegeSerializer
    permission_classes = (AllowAny,)


class DepartmentList(FilterOrderAPIView, generics.ListAPIView):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = (AllowAny,)


class MajorList(FilterOrderAPIView, generics.ListAPIView):
    queryset = Major.objects.all()
    serializer_class = MajorSerializer
    permission_classes = (AllowAny,)


class StaticInformation(generics.RetrieveAPIView):
    def get_queryset(self):
        return []

    def retrieve(self, request, *args, **kwargs):
        params = self.request.query_params
        if 'year' in params and 'semester' in params:
            year, semester = params.get('year'), params.get('semester')
            if not year.isnumeric():
                return Response({'detail': "Invalid year param, expected a number"})

            lectures = Lecture.objects.filter(year=year, semester=semester)
            types = set()
            for t in lectures.values_list('course__type').distinct():
                types.add(t[0])
            fields = {}
            for f in lectures.values_list('course__field').distinct():
                if not f[0]:
                    continue
                f, fd = f[0].split('-')
                if f not in fields:
                    fields[f] = set()
                fields[f].add(fd)
            return Response(dict(
                types=types,
                fields=fields,
            ))
        else:
            colleges = CollegeSerializer(College.objects.all(), many=True).data
            years = {}
            for year, semester in Lecture.objects.values_list('year', 'semester').distinct():
                if year not in years:
                    years[year] = [None]*4
                for i, s in enumerate(settings.SEMESTER_CHOICES):
                    if s[0] == semester:
                        years[year][3-i] = semester
            years_semesters = []
            for year in sorted(years, reverse=True):
                for semester in years[year]:
                    if semester:
                        years_semesters.append(dict(year=year, semester=semester))
            return Response(dict(
                colleges=colleges,
                semesters=years_semesters,
            ))


class RecommendView(generics.ListAPIView):
    serializer_class = RecommendedTimeTableSerializer
    permission_classes = (IsAuthenticated, IsStudent)

    def get_queryset(self):
        options = self.request.query_params.copy()
        student = Student.objects.get_by_natural_key(self.request.user.username)
        from time import time as current
        last = current()
        recommends = recommend(options, student)
        print(current() - last, 's')
        return recommends

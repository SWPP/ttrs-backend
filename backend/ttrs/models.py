from django.contrib.auth.models import User, UserManager
from django.db import models
from django.conf import settings
from django.db.models import Lookup, Field, Avg


@Field.register_lookup
class Abbreviation(Lookup):
    lookup_name = 'abbrev'

    def as_sql(self, compiler, connection):
        lhs, lhs_params = self.process_lhs(compiler, connection)
        rhs, rhs_params = self.process_rhs(connection, connection)
        rhs_params[0] = '%'+'%'.join(rhs_params[0])+'%'
        params = lhs_params + rhs_params
        return '%s like %s' % (lhs, rhs), params


class Student(User):
    class Meta:
        verbose_name = 'Student'

    objects = UserManager()

    college = models.ForeignKey('ttrs.College', related_name='students', on_delete=models.CASCADE)
    department = models.ForeignKey('ttrs.Department', related_name='students', on_delete=models.CASCADE, null=True, blank=True)
    major = models.ForeignKey('ttrs.Major', related_name='students', on_delete=models.CASCADE, null=True, blank=True)
    grade = models.PositiveSmallIntegerField()

    not_recommends = models.ManyToManyField('ttrs.Course', blank=True)


class Course(models.Model):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=50)

    type = models.CharField(max_length=10)
    field = models.CharField(max_length=30, null=True, blank=True)
    grade = models.PositiveSmallIntegerField()
    credit = models.PositiveSmallIntegerField()

    college = models.ForeignKey('ttrs.College', related_name='courses', on_delete=models.CASCADE)
    department = models.ForeignKey('ttrs.Department', related_name='courses', on_delete=models.CASCADE, null=True, blank=True)
    major = models.ForeignKey('ttrs.Major', related_name='courses', on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return self.name


class Lecture(models.Model):
    course = models.ForeignKey('ttrs.Course', related_name='lectures', on_delete=models.CASCADE)
    time_slots = models.ManyToManyField('ttrs.TimeSlot', related_name='lectures', blank=True)

    year = models.PositiveSmallIntegerField()
    semester = models.CharField(max_length=10, choices=settings.SEMESTER_CHOICES)
    number = models.CharField(max_length=10)

    instructor = models.CharField(max_length=20)
    note = models.TextField(blank=True)

    rating = models.FloatField(default=0)

    def update_rating(self):
        if self.evaluations.count():
            self.rating = sum([e.rate for e in self.evaluations.all()])/self.evaluations.count()
        else:
            self.rating = 0
        self.save()

    @staticmethod
    def have_same_course(lectures):
        codes = set()
        for lecture in lectures:
            if lecture.course.code in codes:
                return True
            codes.add(lecture.course.code)
        return False

    @staticmethod
    def do_overlap(lectures):
        whole_days = {}
        for lecture in lectures:
            lecture_days = {}
            for time_slot in lecture.time_slots.all():
                if time_slot.day_of_week not in lecture_days:
                    lecture_days[time_slot.day_of_week] = []
                lecture_days[time_slot.day_of_week].append((time_slot.start_time, 1))
                lecture_days[time_slot.day_of_week].append((time_slot.end_time, 0))
            for day_of_week in lecture_days:
                lecture_days[day_of_week].sort()
                merged_times = []
                cnt = 0
                for time, start in lecture_days[day_of_week]:
                    if start:
                        if cnt == 0:
                            merged_times.append([time])
                        cnt += 1
                    else:
                        cnt -= 1
                        if cnt == 0:
                            merged_times[-1].append(time)
                if day_of_week not in whole_days:
                    whole_days[day_of_week] = []
                whole_days[day_of_week].extend(merged_times)
        for times in whole_days.values():
            times.sort()
            for i in range(len(times)-1):
                if times[i][1] > times[i+1][0]:
                    return True
        return False

    def __str__(self):
        return '{}-{} ({}:{})'.format(self.course, self.instructor, self.year, self.semester)

    class Meta:
        unique_together = ('course', 'year', 'semester', 'number', )


class Evaluation(models.Model):
    author = models.ForeignKey('ttrs.Student', related_name='evaluations', on_delete=models.DO_NOTHING)
    lecture = models.ForeignKey('ttrs.Lecture', related_name='evaluations', on_delete=models.CASCADE)
    rate = models.PositiveSmallIntegerField()
    comment = models.TextField()
    like_it = models.ManyToManyField('ttrs.Student', related_name='like_its', blank=True)
    evaluated_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.lecture.evaluations.count():
            self.lecture.rating = self.lecture.evaluations.aggregate(Avg('rate'))['rate__avg']
        else:
            self.lecture.rating = 0
        models.Model.save(self, *args, **kwargs)
        self.lecture.update_rating()

    def delete(self, *args, **kwargs):
        lecture = self.lecture
        models.Model.delete(self, *args, **kwargs)
        lecture.update_rating()

    def __str__(self):
        return '{}-{}'.format(self.lecture, self.author)

    class Meta:
        unique_together = ('author', 'lecture')


class TimeTable(models.Model):
    title = models.CharField(max_length=100, default='time table', blank=True)
    memo = models.TextField(blank=True)

    year = models.PositiveSmallIntegerField()
    semester = models.CharField(max_length=10, choices=settings.SEMESTER_CHOICES)
    lectures = models.ManyToManyField('ttrs.Lecture', related_name='lectures', blank=True)

    def __init__(self, *args, other=None, **kwargs):
        super().__init__(*args, **kwargs)
        if other is not None:
            # copy data from other TimeTable
            self.title = other.title
            self.memo = other.memo
            self.year = other.year
            self.semester = other.semester
            self.pending_lectures = other.lectures.all()

    def save_m2m(self):
        """
        Supporting save method for copying ManyToManyField.
        """
        self.save()
        self.lectures.set(self.pending_lectures)
        self.save()

    def __str__(self):
        return '{} ({}:{})'.format(self.title, self.year, self.semester)


class MyTimeTable(TimeTable):
    owner = models.ForeignKey('ttrs.Student', related_name='my_time_tables', on_delete=models.CASCADE)
    modified_at = models.DateTimeField(auto_now=True)


class BookmarkedTimeTable(TimeTable):
    owner = models.ForeignKey('ttrs.Student', related_name='bookmarked_time_tables', on_delete=models.CASCADE)
    bookmarked_at = models.DateTimeField(auto_now_add=True)


class ReceivedTimeTable(TimeTable):
    owner = models.ForeignKey('ttrs.Student', related_name='received_time_tables', on_delete=models.CASCADE)
    sender = models.ForeignKey('ttrs.Student', related_name='sent_time_tables', on_delete=models.SET_NULL, null=True)
    sent_at = models.DateTimeField(auto_now_add=True)
    received_at = models.DateTimeField(null=True, blank=True)


class RecommendedTimeTable(TimeTable):
    owner = models.ForeignKey('ttrs.Student', related_name='recommended_time_tables', on_delete=models.CASCADE)
    score = models.IntegerField(default=0)
    recommended_at = models.DateTimeField(auto_now_add=True)


class TimeSlot(models.Model):
    day_of_week = models.CharField(max_length=10)
    start_time = models.CharField(max_length=10)
    end_time = models.CharField(max_length=10)

    classroom = models.ForeignKey('ttrs.Classroom', related_name='time_slots', on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        if self.classroom:
            return '{} {}~{} [{}]'.format(self.day_of_week, self.start_time, self.end_time, self.classroom)
        return '{} {}~{}'.format(self.day_of_week, self.start_time, self.end_time)


class Classroom(models.Model):
    building = models.CharField(max_length=10)
    room_no = models.CharField(max_length=10)

    class Meta:
        unique_together = ('building', 'room_no')

    def __str__(self):
        return '{}-{}'.format(self.building, self.room_no)


class College(models.Model):
    name = models.CharField(max_length=30, unique=True)

    def __str__(self):
        return self.name


class Department(models.Model):
    college = models.ForeignKey('ttrs.College', related_name='departments', on_delete=models.CASCADE)
    name = models.CharField(max_length=30, unique=True)

    def __str__(self):
        return self.name


class Major(models.Model):
    department = models.ForeignKey('ttrs.Department', related_name='majors', on_delete=models.CASCADE)
    name = models.CharField(max_length=30, unique=True)

    def __str__(self):
        return self.name

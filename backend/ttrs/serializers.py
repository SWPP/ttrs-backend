from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from django.core.exceptions import ValidationError as DjangoValidationError, ObjectDoesNotExist

from .models import Student, College, Department, Major, Course, Lecture, Evaluation, TimeTable, MyTimeTable, \
    BookmarkedTimeTable, ReceivedTimeTable, RecommendedTimeTable, TimeSlot, Classroom


class StudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = ('id', 'username', 'password', 'email', 'grade', 'college', 'department', 'major', 'not_recommends',
                  'my_time_tables', 'bookmarked_time_tables', 'received_time_tables')
        read_only_fields = ('my_time_tables', 'bookmarked_time_tables', 'received_time_tables')
        extra_kwargs = {
            'email': {'required': True, 'allow_null': False, 'allow_blank': False}
        }

    def get_field_value(self, data, key):
        if key in data:
            return data[key]
        if self.instance:
            return getattr(self.instance, key)
        return None

    def validate_email(self, email):
        if email.split('@')[1] != 'snu.ac.kr':
            raise ValidationError("The host must be 'snu.ac.kr'.")
        student = Student.objects.filter(email=email).first()
        if student and student != self.instance:
            raise ValidationError("A student with that email already exists.")
        return email

    def validate(self, data):
        # belonging validations of college-department, department-major
        errors = []
        college = self.get_field_value(data, 'college')
        department = self.get_field_value(data, 'department')
        major = self.get_field_value(data, 'major')
        if department:
            if not college or college.id != department.college_id:
                errors.append('The department must belong to the college.')
        if major is not None:
            if not department or department.id != major.department_id:
                errors.append('The major must belong to the department.')
        if errors:
            raise ValidationError({'belonging': errors})

        # password hashing
        if 'password' not in data:
            # password not changed
            return data
        try:
            if self.instance:
                validate_password(data['password'], user=self.instance)
            else:
                tmp_user = User(username=data['username'], email=data['email'])
                validate_password(data['password'], user=tmp_user)
        except DjangoValidationError as ve:
            raise ValidationError({'password': ve.messages})
        data['password'] = make_password(data['password'])
        return data


class CourseSerializer(serializers.ModelSerializer):
    college = serializers.StringRelatedField()
    department = serializers.StringRelatedField()
    major = serializers.StringRelatedField()

    class Meta:
        model = Course
        fields = '__all__'


class ClassroomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Classroom
        fields = '__all__'


class TimeSlotSerializer(serializers.ModelSerializer):
    classroom = ClassroomSerializer()

    class Meta:
        model = TimeSlot
        fields = '__all__'


class LectureSerializer(serializers.ModelSerializer):
    course = CourseSerializer()
    time_slots = TimeSlotSerializer(many=True)

    class Meta:
        model = Lecture
        fields = '__all__'


class EvaluationSerializer(serializers.ModelSerializer):
    author = serializers.StringRelatedField()

    class Meta:
        model = Evaluation
        fields = '__all__'
        read_only_fields = ('author', 'like_it')

    def validate_rate(self, rate):
        if not (1 <= rate <= 10):
            raise ValidationError("The rate should be an integer between 1 and 10 inclusive.")
        return rate

    def validate_lecture(self, lecture):
        # ignore PUT, PATCH
        if self.instance is not None:
            return lecture

        # Only one evaluation per lecture
        username = self.context['request'].user.username
        student = Student.objects.get_by_natural_key(username)
        evaluation = Evaluation.objects.filter(author=student, lecture=lecture).first()
        if evaluation is not None:
            raise ValidationError('You can make at most one evaluation per lecture. '
                                  'Existing evaluation id: {}'.format(evaluation.id))
        return lecture


class EvaluationDetailSerializer(EvaluationSerializer):
    lecture = serializers.ReadOnlyField(source='lecture.id')


class TimeTableSerializer(serializers.ModelSerializer):
    credit_sum = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = TimeTable
        fields = '__all__'
        read_only_fields = ('owner', 'year', 'semester')

    def validate_lectures(self, lectures):
        if not lectures:
            if self.context['request'].method == 'POST':
                raise ValidationError("There should be at least one lecture.")
            return lectures
        year, semester = lectures[0].year, lectures[0].semester
        for lecture in lectures[1:]:
            if lecture.year != year or lecture.semester != semester:
                raise ValidationError("Lectures should share same year and semester.")
        if Lecture.have_same_course(lectures):
            raise ValidationError("All lectures should have distinct courses.")
        if Lecture.do_overlap(lectures):
            raise ValidationError("Time slots of lectures should not overlap.")
        self.year = year
        self.semester = semester
        return lectures

    def create(self, validated_data):
        if hasattr(self, 'year'):
            validated_data['year'] = self.year
        if hasattr(self, 'semester'):
            validated_data['semester'] = self.semester
        return super(TimeTableSerializer, self).create(validated_data)

    def get_credit_sum(self, obj):
        return sum([lecture.course.credit for lecture in obj.lectures.all()])


class MyTimeTableSerializer(TimeTableSerializer):
    class Meta(TimeTableSerializer.Meta):
        model = MyTimeTable

    def validate(self, data):
        if 'title' not in data or not data['title']:
            if not self.instance:
                data['title'] = '{}년 {}'.format(self.year, self.semester)
        return data


class BookmarkedTimeTableSerializer(TimeTableSerializer):
    class Meta(TimeTableSerializer.Meta):
        model = BookmarkedTimeTable
        read_only_fields = TimeTableSerializer.Meta.read_only_fields+('bookmarked_at',)


class ReceivedTimeTableSerializer(TimeTableSerializer):
    sender = serializers.StringRelatedField()

    class Meta(TimeTableSerializer.Meta):
        model = ReceivedTimeTable
        read_only_fields = TimeTableSerializer.Meta.read_only_fields+('sender', 'received_at')


class RecommendedTimeTableSerializer(TimeTableSerializer):
    class Meta(TimeTableSerializer.Meta):
        model = RecommendedTimeTable
        read_only_fields = TimeTableSerializer.Meta.read_only_fields+('score', 'recommended_at')


class CopyTimeTableSerializer(serializers.Serializer):
    time_table_id = serializers.IntegerField()

    def __init__(self, *args, **kwargs):
        self.owner = kwargs.pop('owner')
        super().__init__(*args, **kwargs)

    def validate_time_table_id(self, time_table_id):
        try:
            TimeTable.objects.get(pk=time_table_id)
        except ObjectDoesNotExist:
            raise ValidationError("There is no time table with this id.")
        table_models = (MyTimeTable, BookmarkedTimeTable, ReceivedTimeTable, RecommendedTimeTable)
        if not any([model.objects.filter(owner=self.owner, pk=time_table_id) for model in table_models]):
            raise ValidationError("You can send only your tables.")
        return time_table_id


class SendTimeTableSerializer(CopyTimeTableSerializer):
    receiver_name = serializers.CharField(max_length=150)

    def validate_receiver_name(self, receiver_name):
        try:
            Student.objects.get_by_natural_key(receiver_name)
        except ObjectDoesNotExist:
            raise ValidationError("The receiver with this name does not exist or is not a student.")
        return receiver_name


class SemesterSerializer(serializers.Serializer):
    year = serializers.IntegerField()
    semester = serializers.CharField()


class MajorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Major
        fields = '__all__'


class DepartmentSerializer(serializers.ModelSerializer):
    majors = MajorSerializer(many=True, read_only=True)

    class Meta:
        model = Department
        fields = '__all__'


class CollegeSerializer(serializers.ModelSerializer):
    departments = DepartmentSerializer(many=True, read_only=True)

    class Meta:
        model = College
        fields = '__all__'

import heapq
import pickle
from typing import List

from django.db.models import Avg
from django.http import QueryDict
from rest_framework.exceptions import ValidationError
from ttrs.models import Course, Lecture, RecommendedTimeTable, Student, Evaluation

option_fields = [
    'year',
    'semester',
    'avoid_successive',
    'avoid_void',
    'avoid_first',
    'jeonpil',
    'jeonseon',
    'gyoyang',
    'credit',
    'blocks',
]
day_to_index = dict(월=0, 화=1, 수=2, 목=3, 금=4, 토=5)


class SimpleLecture:
    """
    Simplified Lecture object
    """
    def __init__(self, lecture: Lecture):
        """
        Initiate for static information.
        :param lecture: base Lecture django model object
        """
        self.id = lecture.id
        self.name = lecture.course.name
        self.course = lecture.course_id
        self.grade = lecture.course.grade
        self.college = lecture.course.college_id
        self.department = lecture.course.department_id
        self.major = lecture.course.major_id
        self.type = lecture.course.type
        self.credit = lecture.course.credit
        evaluations = lecture.evaluations.all()
        self.rating = sum([evaluation.rate for evaluation in evaluations]) if evaluations else 0

        time_slot_set = get_time_slot_set(lecture)
        self.first_periods = sum([bool(time_slot_set[day] and (time_slot_set[day][0][0] < 20)) for day in range(6)])
        self.time_slot_set = time_slot_set

        self.score = 0
        self.real_type = None
        self.next_lectures = None

    def init(self, next_lectures: list, info: dict):
        """
        Initiate for an instance of recommendation
        :param next_lectures: lectures which are compatible with this lecture
        :param info: information about the recommendation
        """
        # lecture score calculation
        score = 0

        # student grade
        # if self.type not in ('전선', '전필') or self.department and self.department == info['student_department']:
        #     score -= abs(self.grade-info['student_grade']) * info['grade_weight']

        # student membership
        if self.major and self.major == info['student_major']:
            score += 2
            if self.type == '전선':
                self.real_type = '전선'
                score += 2
            elif self.type == '전필':
                self.real_type = '전필'
                score += 3
        elif self.department and self.department == info['student_department']:
            score += 2
            if self.type == '전선':
                self.real_type = '전선'
                score += 1
            elif self.type == '전필':
                self.real_type = '전필'
                score += 2
        elif self.type in ('전필', '전선'):
            if self.college == info['student_college']:
                score -= 1
            else:
                score -= 2
        if self.type == '교양':
            self.real_type = '교양'
            score += 1

        # rating except unrated lecture
        if self.rating > 0:
            score += (self.rating - info['average_rating']) * info['evaluation_weight']

        # not_recommends
        if self.course in info['not_recommends']:
            score -= 20

        # multiply score with credit
        score *= self.credit

        # first period
        score -= self.first_periods * info['first_period_weight']

        self.score = score
        self.next_lectures = next_lectures

    def __str__(self):
        return self.name+' '+str(self.score)


class Context:
    """
    Immutable node context object for A* algorithm.
    """
    def __init__(self, base=None, lecture: SimpleLecture=None, info: dict=None):
        if base is None:
            # Empty context
            self.lectures = []
            self.credit = 0
            self.credits = dict(전필=0, 전선=0, 교양=0)
            self.table_score = 0
            self.lectures_score = 0
        else:
            # Extend base context with given lecture
            self.lectures = base.lectures+[lecture]
            self.credit = base.credit + lecture.credit
            self.credits = base.credits.copy()
            if lecture.real_type is not None:
                self.credits[lecture.real_type] += lecture.credit
            self.lectures_score = base.lectures_score + lecture.score
            self.table_score = self.get_expected_score(info)

    def compatible(self, lecture: SimpleLecture):
        # Check if new lecture can be included in this table
        for i in range(len(self.lectures) - 1):
            if self.lectures[i].course == lecture.course or intersect(self.lectures[i].time_slot_set, lecture.time_slot_set):
                return False
        return True

    def get_expected_score(self, info):
        # Expected table score calculation based on current state
        table_score = 0
        lectures = self.lectures

        # serial lectures
        serial_score = 0
        for day in range(6):
            slots = []
            for lecture in lectures:
                slots += lecture.time_slot_set[day]
            slots.sort()
            serial = 0
            for i in range(len(slots) - 1):
                if slots[i][1] == slots[i + 1][0]:
                    serial += 1
                else:
                    serial_score += serial
                    serial = 0
            serial_score += serial
        table_score -= serial_score * info['serial_lectures_weight']

        # credit(type)
        credit_score = 0
        remaining_credit = info['expected_credit'] - self.credit
        remaining_type_credit = 0
        count = 0
        for type in self.credits:
            if self.credits[type] > info['credits_weight'][type]:
                credit_score += ((self.credits[type] - info['credits_weight'][type]) ** 2) * info['type_weight']
            else:
                remaining_type_credit += info['credits_weight'][type] - self.credits[type]
                count += 1
        if remaining_credit > 0:
            remaining_type_credit -= remaining_credit
        else:
            credit_score += (-remaining_credit ** 2) * info['credit_weight']
        if remaining_type_credit > 0:
            credit_score += ((remaining_type_credit / count) ** 2) * count * info['type_weight']
        table_score -= credit_score

        return table_score

    def get_final_score(self, info):
        # Final table score calculation
        final_score = 0
        lectures = self.lectures

        # serial/void lectures
        serial_score = 0
        void_score = 0
        for day in range(6):
            slots = []
            for lecture in lectures:
                slots += lecture.time_slot_set[day]
            slots.sort()
            serial = 0
            for i in range(len(slots) - 1):
                if slots[i][1] == slots[i + 1][0]:
                    serial += 1
                else:
                    serial_score += serial
                    serial = 0
                    if slots[i][1] + 3 <= slots[i + 1][0]:
                        void_score += slots[i + 1][0] - slots[i][1]
            serial_score += serial
        final_score -= serial_score * info['serial_lectures_weight']
        final_score -= void_score * info['void_lectures_weight']

        # credit(type)
        credit_score = 0
        for type in self.credits:
            credit_score += (abs(self.credits[type] - info['credits_weight'][type]) ** 2) * info['type_weight']
        credit_score += (abs(self.credit - info['expected_credit']) ** 2) * info['credit_weight']
        final_score -= credit_score

        return self.lectures_score + final_score

    @property
    def score(self):
        return self.table_score + self.lectures_score

    def __lt__(self, other):
        return self.score > other.score

    def __str__(self):
        return '{:.2f} {}'.format(self.score, [lecture.name for lecture in self.lectures])


def recommend(options: QueryDict, student: Student):
    lectures, info = init(options, student)
    contexts = rank_lecture_set(lectures, info)
    contexts.sort(key=lambda c: c[1], reverse=True)
    for i in range(min(10, len(contexts))):
        context = contexts[i]
        print(i, context[0], context[1])

    recommends = []
    for i in range(min(10, len(contexts))):
        time_table = RecommendedTimeTable(owner=student, title='table {}'.format(i), year=info['year'], semester=info['semester'])
        time_table.save()
        time_table.lectures.set([Lecture.objects.get(pk=lecture.id) for lecture in contexts[i][0].lectures])
        recommends.append(time_table)

    return recommends


def init(options: QueryDict, student: Student):
    # Delete old recommendations
    RecommendedTimeTable.objects.filter(owner=student).delete()

    # Collect options
    info = {}
    for option in option_fields:
        if option not in options:
            raise ValidationError({'detail': 'Necessary options are not provided.'})
    try:
        info['student_grade'] = student.grade
        info['student_college'] = student.college_id
        info['student_department'] = student.department_id
        info['student_major'] = student.major_id
        info['not_recommends'] = [course.id for course in student.not_recommends.all()]
        info['year'] = int(options.get('year'))
        info['semester'] = options.get('semester')
        info['grade_weight'] = 1
        info['type_weight'] = 5
        info['credit_weight'] = 3
        info['distance_weight'] = 1
        info['evaluation_weight'] = 1
        info['serial_lectures_weight'] = 2 * (options.get('avoid_successive') == 'true')
        info['void_lectures_weight'] = 3 * (options.get('avoid_void') == 'true')
        info['first_period_weight'] = 15 * (options.get('avoid_first') == 'true')
        info['expected_credit'] = int(options.get('credit'))
        jeonpil = int(options.get('jeonpil'))
        jeonseon = int(options.get('jeonseon'))
        gyoyang = int(options.get('gyoyang'))
        total = jeonpil + jeonseon + gyoyang
        info['credits_weight'] = dict(
            전필=info['expected_credit'] * jeonpil / total,
            전선=info['expected_credit'] * jeonseon / total,
            교양=info['expected_credit'] * gyoyang / total,
        )
        info['blocks'] = [[list(map(int, slot.split(':'))) for slot in slots.split(',')] if slots else [] for slots in
                          options.get('blocks').split('|')]
        info['average_rating'] = Evaluation.objects.aggregate(Avg('rate'))['rate__avg']
    except Exception:
        raise ValidationError({'detail': 'Some options are not valid.'})

    # Load lectures and filter by blocks option
    whole_lectures, whole_compatible = load(info['year'], info['semester'])
    available = []
    for i, lecture in enumerate(whole_lectures):
        available.append(contains(info['blocks'], lecture.time_slot_set))

    # Init lectures
    lectures = []
    for i, lecture in enumerate(whole_lectures):
        if not available[i]:
            continue
        next_lectures = []
        for j in whole_compatible[i]:
            if available[j]:
                next_lectures.append(whole_lectures[j])
        lecture.init(next_lectures, info)
        lectures.append(lecture)

    return lectures, info


def save(year, semester):
    """
    Save list of SimpleLecture object to external resource (using pickle).
    """
    lectures = [SimpleLecture(lecture) for lecture in Lecture.objects.filter(year=year, semester=semester) if lecture.time_slots.count() > 0]
    with open('lectures{}{}.pickle'.format(year, semester), 'wb') as f:
        pickle.dump(lectures, f)
    distinct = []
    for i, lecture1 in enumerate(lectures):
        indices = []
        for j in range(i + 1, len(lectures)):
            lecture2 = lectures[j]
            if lecture1.course != lecture2.course and not intersect(lecture1.time_slot_set, lecture2.time_slot_set):
                indices.append(j)
        distinct.append(indices)
        print('{}/{}'.format(i, len(lectures)), len(indices), len(indices)*100//len(lectures))
    with open('compatible{}{}.pickle'.format(year, semester), 'wb') as f:
        pickle.dump(distinct, f)


def load(year, semester):
    """
    Load list of SimpleLecture object and their compatible lecture list
    from external resource  (using pickle).
    """
    while True:
        try:
            with open('lectures{}{}.pickle'.format(year, semester), 'rb') as f:
                whole_lectures = pickle.load(f)
            with open('compatible{}{}.pickle'.format(year, semester), 'rb') as f:
                whole_compatible = pickle.load(f)
            break
        except Exception as e:
            save(year, semester)
    return whole_lectures, whole_compatible


def rank_lecture_set(lectures: List[SimpleLecture], info: dict):
    """
    Using A* algorithm, rank lecture sets and return the list.
    :param lectures: Whole available lecture list
    :param info: information about the recommendation
    :return: Ranked lecture set list
    """
    contexts = []
    base = Context()
    for lecture in lectures:
        heapq.heappush(contexts, Context(base, lecture, info))
    ranks = []
    max_score = -1000000000
    for count in range(500):
        if not contexts:
            break
        context = heapq.heappop(contexts)
        final_score = context.get_final_score(info)
        max_score = max(max_score, final_score)
        ranks.append((context, final_score))

        # print(count, final_score, context)
        for lecture in context.lectures[-1].next_lectures:
            if context.compatible(lecture) and context.credit + lecture.credit <= info['expected_credit']:
                heapq.heappush(contexts, Context(context, lecture, info))
    return ranks


def time_to_int(time: str):
    h, m = map(int, time.split(':'))
    return (h * 60 + m - 1) // 30 + 1


def get_time_slot_set(lecture: Lecture):
    """
    Given lecture, Simplify time_slots
    """
    time_slot_set = [[], [], [], [], [], []]
    for time_slot in lecture.time_slots.all():
        day_index = day_to_index[time_slot.day_of_week]
        start_int = time_to_int(time_slot.start_time)
        end_int = time_to_int(time_slot.end_time)
        time_slot_set[day_index].append((start_int, end_int))
    for i, time_slots in enumerate(time_slot_set):
        if not time_slots:
            continue
        time_slots.sort()
        new_time_slots = []

        start, end = time_slots[0]
        for time_slot in time_slots[1:]:
            if end < time_slot[0]:
                new_time_slots.append((start, end))
                start, end = time_slot
            else:
                end = max(end, time_slot[1])
        new_time_slots.append((start, end))
        time_slot_set[i] = new_time_slots
    return time_slot_set


def contains(slot_set1: List[List[tuple]], slot_set2: List[List[tuple]]):
    """
    Returns if slot_set1 contains slot_set2.
    """
    for day in range(6):
        slots1 = slot_set1[day]
        slots2 = slot_set2[day]
        if not slots1:
            if slots2:
                return False
            continue
        i, j = 0, 0
        while i < len(slots1) and j < len(slots2):
            if slots1[i][0] > slots2[j][0]:
                return False
            if slots1[i][1] < slots2[j][0]:
                i += 1
            else:
                if slots1[i][1] < slots2[j][1]:
                    return False
                j += 1
        if j < len(slots2):
            return False
    return True


def intersect(slot_set1: List[List[tuple]], slot_set2: List[List[tuple]]):
    """
    Returns if slot_set1 and slot_set2 intersects.
    """
    for day in range(6):
        slots1 = slot_set1[day]
        slots2 = slot_set2[day]
        if not slots1 or not slots2:
            continue
        i, j = 0, 0
        while i < len(slots1) and j < len(slots2):
            if slots1[i][0] < slots2[j][0]:
                if slots1[i][1] > slots2[j][0]:
                    return True
                i += 1
            else:
                if slots1[i][0] < slots2[j][1]:
                    return True
                j += 1
    return False

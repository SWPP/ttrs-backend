import random, heapq
from functools import reduce

from django.db.models import Max, Min, Q
from ttrs.models import Course, Lecture, RecommendedTimeTable


# Option fields and their default values
option_field = {
    'year': 2018,
    'semester': '1학기',
    'expected_credit': 15,
    'credit_weight': 0,
    'distance_weight': 0,
    'evaluation_weight': 0,
    'first_period_weight': 0,
    'serial_lectures_weight': 0,
}


def recommend(options, student):
    info = init(options, student)
    # print(info)
    recommends = []

    candidates = build_candidates(info)
    candidates.sort(key=lambda x: get_score(x, info), reverse=True)

    index = 0
    candidates = candidates[:3]
    for candidate in candidates:
        time_table = RecommendedTimeTable(owner=student, title='table {}'.format(index), year=info['year'], semester=info['semester'])
        time_table.save()
        time_table.lectures.set(candidate)
        recommends.append(time_table)
        index += 1

    return recommends


def init(options, student):
    RecommendedTimeTable.objects.filter(owner=student).delete()

    info = {}
    # Collect information
    for option in option_field.keys():
        info[option] = options[option] if options.get(option) else option_field[option]
        if option != 'semester':
            info[option] = int(info[option])

    # lectures = Lecture.objects.filter(year=info['year'], semester=info['semester'])
    # info['min_id'] = lectures.aggregate(min_id=Min('id'))['min_id']
    # info['max_id'] = lectures.aggregate(max_id=Max('id'))['max_id']

    # Collect information from student
    info['student_grade'] = student.grade
    info['student_college'] = student.college
    info['student_department'] = student.department if student.department else None
    info['student_major'] = student.major if student.major else None
    info['not_recommends'] = student.not_recommends

    return info


def build_candidates(info):
    """
    Build candidate lecture sets from seed sets.
    Seed sets are courses/lectures that get high scores with regard to given user info.
    """
    seed_courses = get_seed_courses(10, info)
    # print(seed_courses)

    candidates = []
    seed_lectures = Lecture.objects.filter(reduce(lambda x, y: x | y, [Q(course=c) for c in seed_courses]))
    seed_lectures = seed_lectures.filter(year=info['year'], semester=info['semester'])
    for lecture in seed_lectures:
        candidate = branch_and_bound_help([lecture, ], lecture.course.credit, seed_lectures, info)
        candidates.append(candidate)

    return candidates


def get_seed_courses(num_seeds, info):
    course_heap = []

    courses = Course.objects.all()
    for course in courses:
        elt = CourseElt(course=course, score=get_course_score(course, info))
        heapq.heappush(course_heap, elt)
        if num_seeds < len(course_heap):
            heapq.heappop(course_heap)

    return [elt.course for elt in course_heap]


def get_course_score(course, info):
    """
    Given course, calculates score for the course.
    """
    score = 0
    score -= abs(course.grade - info['student_grade'])

    if course.department == info['student_department'] and course.type == '전필':
        score += 8
    if course.department == info['student_department'] and course.type == '전선':
        score += 4
    if course.type == '교양':
        score += 2

    if course in info['not_recommends'].all():
        score = 0

    return score


max_expect = 0
max_score = 0
max_lectures = []


def branch_and_bound_help(initial_lectures, initial_credit, seed_lectures, info):
    """
    This is a wrapper function for branch_and_bound.
    """
    global max_expect
    global max_score
    global max_lectures

    max_expect = 0
    max_score = 0
    max_lectures = []

    # print('!!!!!seed:', initial_lectures)
    branch_and_bound(initial_lectures, initial_credit, seed_lectures, info)
    # print('!!!!!max_lectures:', max_lectures)

    return max_lectures


def branch_and_bound(current_lectures, current_credits, seed_lectures, info):
    """
    Recursively searches through possible lecture sets using basic branch and bound Algorithm
    """
    global max_expect
    global max_score
    global max_lectures

    expected_scores = []
    next = []
    for seed in seed_lectures:
        # If lecture set is invalid, continue.
        if Lecture.have_same_course(current_lectures + [seed]) or Lecture.do_overlap(current_lectures + [seed]):
            continue

        next_credits = current_credits + seed.course.credit
        if next_credits <= info['expected_credit']:
            # In case we can add more lectures
            next_lectures = current_lectures + [seed]
            next.append((next_lectures, next_credits))
            expected_score = upper_bound(next_lectures, info)
            expected_scores.append(expected_score)
            if max_expect < expected_score:
                max_expect = expected_score
        else:
            # In case we cannot add more lectures; that is, we are in the leaf node.
            current_score = get_score(current_lectures, info)
            if max_score < current_score:
                max_score = current_score
                max_lectures = current_lectures

    while len(expected_scores) != 0:
        index = expected_scores.index(max(expected_scores))
        expected_score = expected_scores[index]
        if max_score < expected_score:
            # We branch only if expected score is higher than current max score.
            next_lectures = next[index][0]
            next_credits = next[index][1]
            branch_and_bound(next_lectures, next_credits, seed_lectures, info)

        del expected_scores[index]
        del next[index]

    return


def upper_bound(lectures, info):
    """
    Given a set of lectures, calculates upper bound of its score.
    """
    # TODO: Elaborate upper_bound
    return get_score(lectures, info) + 0


def get_score(lectures, info):
    total_score = 0
    total_credit = 0
    for lecture in lectures:
        lecture_score = 0
        course = lecture.course
        total_credit += course.credit

        if course.type == '교양':
            lecture_score += 1
        if course.department and info['student_department'] and course.department == info['student_department']:
            # print(course.department, student.department)
            lecture_score += 2
        if course.major and info['student_major'] and course.major == info['student_major']:
            # print(course.major, student.major)
            lecture_score += 3
            if course.type == '전선':
                lecture_score += 3
            if course.type == '전필':
                lecture_score += 6

        # Reduce lecture score if it has first period.
        for time_slot in lecture.time_slots.all():
            if time_slot.start_time < '10:00':
                total_score -= info['first_period_weight']

        # Reduce lecture score if it has bad evaluations.
        evaluations = lecture.evaluations.all()
        if len(evaluations) != 0:
            rate = 0
            for evaluation in evaluations:
                rate += evaluation.rate
            rate /= len(lecture.evaluations.all())
            lecture_score -= (5-rate)*info['evaluation_weight']

        # Add lecture score to total score.
        total_score += lecture_score*course.credit

    # Reduce total score if there are serial lectures.
    serial_lectures = get_serial_lectures(lectures)
    for pair in serial_lectures:
        total_score -= info['serial_lectures_weight']

    # TODO: Reduce total score if classrooms are far away

    # Reduce total score if total credit is different from expected credit.
    total_score -= abs(total_credit-info['expected_credit'])*info['credit_weight']
    return total_score


def get_serial_lectures(lectures):
    """
    Given time_table, returns a set of pairs of temporally adjacent lectures.
    :param lectures: A set of lectures
    :return serial_lectures: A set of pairs of lectures those are temporally adjacent.
    """
    serial_lectures = set()

    for lec1 in lectures:
        for lec2 in lectures:
            if lec1 == lec2:
                continue

            for time_slot1 in lec1.time_slots.all():
                start_time1 = list(map(int, time_slot1.start_time.split(':')))
                start_time1 = 60*start_time1[0] + start_time1[1]
                end_time1 = list(map(int, time_slot1.end_time.split(':')))
                end_time1 = 60*end_time1[0] + end_time1[1]

                for time_slot2 in lec2.time_slots.all():
                    start_time2 = list(map(int, time_slot2.start_time.split(':')))
                    start_time2 = 60*start_time2[0] + start_time2[1]
                    end_time2 = list(map(int, time_slot2.end_time.split(':')))
                    end_time2 = 60*end_time2[0] + end_time2[1]

                    # Check if a pair of lectures are temporally adjacent.
                    if end_time1 < start_time2 < end_time1 + 30:
                        serial_lectures.add((lec1.id, lec2.id))

                    if end_time2 < start_time1 < end_time2 + 30:
                        serial_lectures.add((lec2.id, lec1.id))

    # print(serial_lectures)
    return serial_lectures


class CourseElt(object):
    def __init__(self, course, score):
        self.course = course
        self.score = score

    def __lt__(self, other):
        return self.score < other.score

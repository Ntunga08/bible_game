from datetime import timedelta

from django.db import transaction
from django.db.models import F
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.questions.models import Question

from .models import GameSession, SessionQuestion, UserQuestionHistory


QUESTIONS_PER_LEVEL = 10
PASSING_SCORE = 7
MAX_LEVEL = 5


def start_game(user, level=1):
    if level < 1 or level > MAX_LEVEL:
        raise ValidationError({'level': 'Level must be between 1 and 5.'})
    if level > user.highest_level_unlocked:
        raise ValidationError({'level': 'This level is not unlocked yet.'})

    return GameSession.objects.create(
        user=user,
        current_level=level,
        difficulty_level=level,
        score=0,
        total_questions=QUESTIONS_PER_LEVEL,
        correct_answers=0,
        status='active',
    )


def get_session_for_user(session_id, user):
    try:
        return GameSession.objects.get(id=session_id, user=user)
    except GameSession.DoesNotExist as exc:
        raise ValidationError({'session_id': 'Active game session not found.'}) from exc


@transaction.atomic
def serve_questions(session):
    ensure_active(session)

    existing_current_level = SessionQuestion.objects.select_related('question').filter(
        session=session,
        question__difficulty=session.current_level,
    )
    unanswered = existing_current_level.filter(selected_index__isnull=True)
    if unanswered.exists():
        return list(unanswered.order_by('order')[:QUESTIONS_PER_LEVEL])

    used_ids = SessionQuestion.objects.filter(session=session).values_list(
        'question_id',
        flat=True,
    )
    questions = list(
        Question.objects.filter(
            difficulty=session.current_level,
            status='approved',
        )
        .exclude(id__in=used_ids)
        .order_by('times_served', '?')[:QUESTIONS_PER_LEVEL]
    )

    if len(questions) < QUESTIONS_PER_LEVEL:
        raise ValidationError(
            {
                'detail': (
                    f'Not enough approved unused questions for level '
                    f'{session.current_level}.'
                )
            }
        )

    Question.objects.filter(id__in=[question.id for question in questions]).update(
        times_served=F('times_served') + 1
    )

    session_questions = [
        SessionQuestion(
            session=session,
            question=question,
            order=index,
        )
        for index, question in enumerate(questions, start=1)
    ]
    SessionQuestion.objects.bulk_create(session_questions)

    for question in questions:
        history, created = UserQuestionHistory.objects.get_or_create(
            user=session.user,
            question=question,
        )
        if not created:
            history.times_seen = F('times_seen') + 1
            history.save(update_fields=['times_seen', 'last_seen_at'])

    return session_questions


@transaction.atomic
def submit_answer(session, question_id, selected_index):
    ensure_active(session)

    try:
        session_question = SessionQuestion.objects.select_related('question').get(
            session=session,
            question_id=question_id,
        )
    except SessionQuestion.DoesNotExist as exc:
        raise ValidationError(
            {'question_id': 'Question was not served in this session.'}
        ) from exc

    if session_question.selected_index is not None:
        raise ValidationError({'question_id': 'This question was already answered.'})

    question = session_question.question
    is_correct = selected_index == question.correct_index

    session_question.selected_index = selected_index
    session_question.is_correct = is_correct
    session_question.answered_at = timezone.now()
    session_question.save(
        update_fields=['selected_index', 'is_correct', 'answered_at']
    )

    if is_correct:
        GameSession.objects.filter(id=session.id).update(
            correct_answers=F('correct_answers') + 1,
            score=F('score') + 10,
            xp_earned=F('xp_earned') + 10,
        )
        Question.objects.filter(id=question.id).update(
            times_correct=F('times_correct') + 1
        )
        UserQuestionHistory.objects.filter(
            user=session.user,
            question=question,
        ).update(times_correct=F('times_correct') + 1)
        session.user.total_xp = F('total_xp') + 10
        session.user.save(update_fields=['total_xp'])
    else:
        Question.objects.filter(id=question.id).update(
            times_incorrect=F('times_incorrect') + 1
        )

    session.refresh_from_db()
    return session_question


@transaction.atomic
def complete_level(session):
    ensure_active(session)

    answered_count = SessionQuestion.objects.filter(
        session=session,
        question__difficulty=session.current_level,
        selected_index__isnull=False,
    ).count()
    if answered_count < QUESTIONS_PER_LEVEL:
        raise ValidationError({'detail': 'Answer all 10 questions before completing.'})

    if session.correct_answers < PASSING_SCORE:
        session.status = 'failed'
        session.ended_at = timezone.now()
        session.save(update_fields=['status', 'ended_at'])
        return {'status': 'failed', 'next_level': None}

    if session.current_level >= MAX_LEVEL:
        session.status = 'completed'
        session.ended_at = timezone.now()
        session.completed_at = session.ended_at
        session.save(update_fields=['status', 'ended_at', 'completed_at'])
        _update_user_progress(session, completed_level_5=True)
        return {'status': 'passed', 'next_level': None}

    session.current_level += 1
    session.difficulty_level = session.current_level
    session.correct_answers = 0
    session.save(update_fields=['current_level', 'difficulty_level', 'correct_answers'])
    _update_user_progress(session)
    return {'status': 'passed', 'next_level': session.current_level}


@transaction.atomic
def retry_level(session):
    if session.status not in ['active', 'failed']:
        raise ValidationError({'detail': 'Only active or failed sessions can be retried.'})

    session.status = 'active'
    session.correct_answers = 0
    session.save(update_fields=['status', 'correct_answers'])
    return serve_questions(session)


def ensure_active(session):
    if session.status != 'active':
        raise ValidationError({'detail': 'This game session is not active.'})


def _update_user_progress(session, completed_level_5=False):
    user = session.user
    today = timezone.localdate()
    yesterday = today - timedelta(days=1)
    if user.last_played_date == today:
        new_streak = user.current_streak
    elif user.last_played_date == yesterday:
        new_streak = user.current_streak + 1
    else:
        new_streak = 1

    user.highest_level_unlocked = max(
        user.highest_level_unlocked,
        session.current_level,
    )
    user.current_streak = new_streak
    user.longest_streak = max(user.longest_streak, new_streak)
    user.last_played_date = today
    update_fields = [
        'highest_level_unlocked',
        'current_streak',
        'longest_streak',
        'last_played_date',
    ]
    if completed_level_5:
        user.has_unlocked_daily_challenge = True
        user.level_5_completed_at = timezone.now()
        update_fields.extend(
            [
                'has_unlocked_daily_challenge',
                'level_5_completed_at',
            ]
        )
    user.save(
        update_fields=update_fields
    )

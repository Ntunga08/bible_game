import random

from django.db import transaction
from django.db.utils import IntegrityError
from django.db.models import F
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.questions.models import Question

from .models import (
    DailyChallenge,
    DailyChallengeAnswer,
    DailyChallengeAttempt,
    DailyChallengeQuestion,
)


TOTAL_QUESTIONS = 15
HARD_QUESTIONS = 5
MASTER_QUESTIONS = 10


def ensure_daily_unlocked(user):
    if not user.has_unlocked_daily_challenge:
        raise PermissionDenied(
            {'detail': 'Complete Level 5 to unlock the daily challenge.'}
        )


@transaction.atomic
def get_or_create_today_challenge():
    today = timezone.localdate()
    challenge = DailyChallenge.objects.filter(date=today).first()
    if challenge:
        if not challenge.is_active:
            raise ValidationError({'detail': 'Today\'s daily challenge is inactive.'})
        return challenge

    challenge = DailyChallenge.objects.create(
        date=today,
        title=f'Daily Master Challenge - {today.isoformat()}',
    )
    questions = select_daily_questions(today)
    DailyChallengeQuestion.objects.bulk_create(
        [
            DailyChallengeQuestion(
                challenge=challenge,
                question=question,
                order=index,
            )
            for index, question in enumerate(questions, start=1)
        ]
    )
    Question.objects.filter(id__in=[question.id for question in questions]).update(
        times_served=F('times_served') + 1
    )
    return challenge


def create_today_challenge_if_missing():
    today = timezone.localdate()
    challenge = DailyChallenge.objects.filter(date=today).first()
    if challenge:
        return challenge, False
    return get_or_create_today_challenge(), True


def select_daily_questions(day):
    level_4 = list(eligible_questions().filter(difficulty=4))
    level_5 = list(eligible_questions().filter(difficulty=5))

    if len(level_4) < HARD_QUESTIONS:
        raise ValidationError(
            {'detail': 'Not enough approved non-AI Level 4 questions for daily challenge.'}
        )
    if len(level_5) < MASTER_QUESTIONS:
        raise ValidationError(
            {'detail': 'Not enough approved non-AI Level 5 questions for daily challenge.'}
        )

    seed = int(day.strftime('%Y%m%d'))
    rng = random.Random(seed)
    selected = rng.sample(level_4, HARD_QUESTIONS) + rng.sample(level_5, MASTER_QUESTIONS)
    rng.shuffle(selected)
    return selected


def eligible_questions():
    return Question.objects.filter(
        status='approved',
        difficulty__in=[4, 5],
        ai_generated=False,
    ).order_by('id')


@transaction.atomic
def start_daily_attempt(user):
    ensure_daily_unlocked(user)
    challenge = get_or_create_today_challenge()
    if DailyChallengeAttempt.objects.filter(user=user, challenge=challenge).exists():
        raise ValidationError({'detail': 'You already attempted today\'s challenge.'})

    attempt = DailyChallengeAttempt.objects.create(
        user=user,
        challenge=challenge,
        total_questions=TOTAL_QUESTIONS,
    )
    return attempt


@transaction.atomic
def answer_daily_question(user, attempt_id, question_id, selected_index, time_taken_seconds=None):
    ensure_daily_unlocked(user)
    attempt = get_attempt_for_user(user, attempt_id)
    if attempt.completed_at is not None:
        raise ValidationError({'detail': 'This daily challenge attempt is already complete.'})

    challenge_question = DailyChallengeQuestion.objects.select_related('question').filter(
        challenge=attempt.challenge,
        question_id=question_id,
    ).first()
    if challenge_question is None:
        raise ValidationError(
            {'question_id': 'Question does not belong to this daily challenge.'}
        )

    question = challenge_question.question
    is_correct = selected_index == question.correct_index
    try:
        DailyChallengeAnswer.objects.create(
            attempt=attempt,
            question=question,
            selected_index=selected_index,
            is_correct=is_correct,
            time_taken_seconds=time_taken_seconds,
        )
    except IntegrityError as exc:
        raise ValidationError(
            {'question_id': 'This question was already answered.'}
        ) from exc

    if is_correct:
        Question.objects.filter(id=question.id).update(
            times_correct=F('times_correct') + 1
        )
    else:
        Question.objects.filter(id=question.id).update(
            times_incorrect=F('times_incorrect') + 1
        )

    return question, is_correct


@transaction.atomic
def complete_daily_attempt(user, attempt_id, time_taken_seconds):
    ensure_daily_unlocked(user)
    attempt = get_attempt_for_user(user, attempt_id)
    if attempt.completed_at is not None:
        raise ValidationError({'detail': 'This daily challenge attempt is already complete.'})

    answered_count = attempt.answers.count()
    if answered_count < attempt.total_questions:
        raise ValidationError({'detail': 'Answer all 15 questions before completing.'})

    correct_answers = attempt.answers.filter(is_correct=True).count()
    wrong_answers = attempt.answers.filter(is_correct=False).count()
    attempt.score = correct_answers
    attempt.correct_answers = correct_answers
    attempt.wrong_answers = wrong_answers
    attempt.time_taken_seconds = time_taken_seconds
    attempt.completed_at = timezone.now()
    attempt.save(
        update_fields=[
            'score',
            'correct_answers',
            'wrong_answers',
            'time_taken_seconds',
            'completed_at',
        ]
    )
    if correct_answers:
        user.total_xp = F('total_xp') + (correct_answers * 10)
        user.save(update_fields=['total_xp'])
    return attempt


def get_attempt_for_user(user, attempt_id):
    try:
        return DailyChallengeAttempt.objects.select_related('challenge').get(
            id=attempt_id,
            user=user,
        )
    except DailyChallengeAttempt.DoesNotExist as exc:
        raise ValidationError({'attempt_id': 'Daily challenge attempt not found.'}) from exc


def todays_completed_attempts():
    return DailyChallengeAttempt.objects.select_related('user', 'challenge').filter(
        challenge__date=timezone.localdate(),
        completed_at__isnull=False,
    ).order_by(
        '-score',
        '-correct_answers',
        'time_taken_seconds',
        'completed_at',
    )


def rank_for_attempt(attempt):
    ranked_ids = list(todays_completed_attempts().values_list('id', flat=True))
    try:
        return ranked_ids.index(attempt.id) + 1
    except ValueError:
        return None

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.questions.models import Category, Question

from .models import (
    DailyChallenge,
    DailyChallengeAnswer,
    DailyChallengeAttempt,
    DailyChallengeQuestion,
)


User = get_user_model()


class DailyChallengeApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='daily-player',
            email='daily@example.com',
            password='StrongPass123!',
            has_unlocked_daily_challenge=True,
        )
        self.locked_user = User.objects.create_user(
            username='locked-player',
            email='locked@example.com',
            password='StrongPass123!',
        )
        self.category = Category.objects.create(
            name='gospel',
            display_name='Gospel',
            icon='cross',
        )
        self.create_questions(level=1, count=8)
        self.create_questions(level=4, count=8)
        self.create_questions(level=5, count=13)
        self.create_questions(level=5, count=2, ai_generated=True)
        self.client.force_authenticate(user=self.user)

    def create_questions(self, level, count, ai_generated=False):
        Question.objects.bulk_create(
            [
                Question(
                    question_text=f'Level {level} question {index} ai {ai_generated}',
                    options=['A', 'B', 'C', 'D'],
                    correct_index=index % 4,
                    explanation=f'Explanation {index}',
                    bible_reference='John 3:16',
                    full_verse_text='',
                    difficulty=level,
                    testament='new',
                    category=self.category,
                    cognitive_type='analysis',
                    topic_tags=['daily'],
                    book_name='John',
                    status='approved',
                    quality_score=4.8,
                    ai_generated=ai_generated,
                )
                for index in range(count)
            ]
        )

    def test_locked_user_cannot_access_daily_challenge(self):
        self.client.force_authenticate(user=self.locked_user)

        response = self.client.get(reverse('daily-today'))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_today_creates_strong_stable_challenge_without_answers(self):
        response = self.client.get(reverse('daily-today'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_questions'], 15)
        self.assertFalse(response.data['already_attempted'])
        self.assertNotIn('correct_index', response.data['questions'][0])

        challenge = DailyChallenge.objects.get(id=response.data['challenge_id'])
        question_ids = DailyChallengeQuestion.objects.filter(
            challenge=challenge,
        ).values_list('question_id', flat=True)
        self.assertEqual(
            Question.objects.filter(id__in=question_ids, difficulty=4).count(),
            5,
        )
        self.assertEqual(
            Question.objects.filter(id__in=question_ids, difficulty=5).count(),
            10,
        )
        self.assertFalse(
            Question.objects.filter(id__in=question_ids, ai_generated=True).exists()
        )

        second_response = self.client.get(reverse('daily-today'))
        self.assertEqual(
            [item['id'] for item in response.data['questions']],
            [item['id'] for item in second_response.data['questions']],
        )

    def test_start_answer_complete_and_leaderboard(self):
        start_response = self.client.post(reverse('daily-start'))
        self.assertEqual(start_response.status_code, status.HTTP_201_CREATED)
        attempt_id = start_response.data['attempt_id']
        questions = start_response.data['questions']
        self.assertEqual(len(questions), 15)

        duplicate_start = self.client.post(reverse('daily-start'))
        self.assertEqual(duplicate_start.status_code, status.HTTP_400_BAD_REQUEST)

        for question_data in questions:
            question = Question.objects.get(id=question_data['id'])
            answer_response = self.client.post(
                reverse('daily-answer'),
                {
                    'attempt_id': attempt_id,
                    'question_id': question.id,
                    'selected_index': question.correct_index,
                    'time_taken_seconds': 5,
                },
                format='json',
            )
            self.assertEqual(answer_response.status_code, status.HTTP_200_OK)
            self.assertTrue(answer_response.data['is_correct'])
            self.assertIn('correct_index', answer_response.data)

        self.assertEqual(DailyChallengeAnswer.objects.count(), 15)
        complete_response = self.client.post(
            reverse('daily-complete'),
            {'attempt_id': attempt_id, 'time_taken_seconds': 420},
            format='json',
        )
        self.assertEqual(complete_response.status_code, status.HTTP_200_OK)
        self.assertEqual(complete_response.data['score'], 15)
        self.assertEqual(complete_response.data['rank_today'], 1)

        leaderboard_response = self.client.get(reverse('daily-leaderboard'))
        self.assertEqual(leaderboard_response.status_code, status.HTTP_200_OK)
        self.assertEqual(leaderboard_response.data[0]['rank'], 1)
        self.assertEqual(leaderboard_response.data[0]['username'], self.user.username)

        history_response = self.client.get(reverse('daily-history'))
        self.assertEqual(history_response.status_code, status.HTTP_200_OK)
        self.assertEqual(history_response.data[0]['score'], 15)

    def test_generate_daily_challenge_command_is_idempotent(self):
        call_command('generate_daily_challenge')
        call_command('generate_daily_challenge')

        self.assertEqual(DailyChallenge.objects.count(), 1)
        self.assertEqual(DailyChallengeAttempt.objects.count(), 0)
        self.assertEqual(DailyChallengeQuestion.objects.count(), 15)

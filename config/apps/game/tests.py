from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.questions.models import Category, Question

from .models import GameSession, SessionQuestion


User = get_user_model()


class GameEngineApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='player',
            email='player@example.com',
            password='StrongPass123!',
        )
        self.category = Category.objects.create(
            name='gospel',
            display_name='Gospel',
            icon='cross',
        )
        self.client.force_authenticate(user=self.user)
        for level in range(1, 6):
            self.create_questions(level=level, count=25)

    def create_questions(self, level, count):
        questions = []
        for index in range(count):
            questions.append(
                Question(
                    question_text=f'Level {level} question {index}',
                    options=['A', 'B', 'C', 'D'],
                    correct_index=index % 4,
                    explanation=f'Explanation {index}',
                    bible_reference='John 3:16',
                    full_verse_text='',
                    difficulty=level,
                    testament='new',
                    category=self.category,
                    cognitive_type='recall',
                    topic_tags=['game'],
                    book_name='John',
                    status='approved',
                    quality_score=4.5,
                    ai_generated=False,
                )
            )
        Question.objects.bulk_create(questions)

    def start_session(self):
        response = self.client.post(reverse('game-start'))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        return response.data['session_id']

    def get_questions(self, session_id):
        response = self.client.get(
            reverse('game-questions', kwargs={'session_id': session_id})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return response

    def answer_questions(self, session_id, questions, correct_count):
        for index, question in enumerate(questions):
            db_question = Question.objects.get(id=question['id'])
            selected_index = (
                db_question.correct_index if index < correct_count else
                (db_question.correct_index + 1) % 4
            )
            response = self.client.post(
                reverse('game-answer'),
                {
                    'session_id': session_id,
                    'question_id': question['id'],
                    'selected_index': selected_index,
                },
                format='json',
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn('correct_index', response.data)

    def test_start_game_creates_active_level_one_session(self):
        response = self.client.post(reverse('game-start'))

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        session = GameSession.objects.get(id=response.data['session_id'])
        self.assertEqual(session.user, self.user)
        self.assertEqual(session.current_level, 1)
        self.assertEqual(session.score, 0)
        self.assertEqual(session.status, 'active')

    def test_get_questions_serves_ten_without_correct_index(self):
        session_id = self.start_session()

        response = self.get_questions(session_id)

        self.assertEqual(len(response.data), 10)
        self.assertNotIn('correct_index', response.data[0])
        self.assertNotIn('explanation', response.data[0])
        self.assertEqual(SessionQuestion.objects.count(), 10)
        served_ids = [item['id'] for item in response.data]
        self.assertEqual(
            Question.objects.filter(id__in=served_ids, times_served=1).count(),
            10,
        )

    def test_submit_answer_updates_session_and_question_counts(self):
        session_id = self.start_session()
        question = self.get_questions(session_id).data[0]
        db_question = Question.objects.get(id=question['id'])

        response = self.client.post(
            reverse('game-answer'),
            {
                'session_id': session_id,
                'question_id': question['id'],
                'selected_index': db_question.correct_index,
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['is_correct'])
        session = GameSession.objects.get(id=session_id)
        db_question.refresh_from_db()
        self.assertEqual(session.correct_answers, 1)
        self.assertEqual(session.score, 10)
        self.assertEqual(db_question.times_correct, 1)

    def test_complete_level_passes_and_moves_to_next_level(self):
        session_id = self.start_session()
        questions = self.get_questions(session_id).data
        self.answer_questions(session_id, questions, correct_count=7)

        response = self.client.post(
            reverse('game-complete-level', kwargs={'session_id': session_id})
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {'status': 'passed', 'next_level': 2})
        session = GameSession.objects.get(id=session_id)
        self.assertEqual(session.current_level, 2)
        self.assertEqual(session.correct_answers, 0)
        self.assertEqual(session.status, 'active')

    def test_complete_level_fails_below_seven_correct(self):
        session_id = self.start_session()
        questions = self.get_questions(session_id).data
        self.answer_questions(session_id, questions, correct_count=6)

        response = self.client.post(
            reverse('game-complete-level', kwargs={'session_id': session_id})
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {'status': 'failed', 'next_level': None})
        self.assertEqual(GameSession.objects.get(id=session_id).status, 'failed')

    def test_retry_keeps_level_and_returns_new_questions(self):
        session_id = self.start_session()
        first_questions = self.get_questions(session_id).data
        self.answer_questions(session_id, first_questions, correct_count=3)
        self.client.post(
            reverse('game-complete-level', kwargs={'session_id': session_id})
        )

        response = self.client.post(
            reverse('game-retry', kwargs={'session_id': session_id})
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 10)
        first_ids = {question['id'] for question in first_questions}
        retry_ids = {question['id'] for question in response.data}
        self.assertTrue(first_ids.isdisjoint(retry_ids))
        session = GameSession.objects.get(id=session_id)
        self.assertEqual(session.current_level, 1)
        self.assertEqual(session.status, 'active')
        self.assertEqual(session.correct_answers, 0)

    def test_level_five_pass_marks_session_completed(self):
        session_id = self.start_session()
        session = GameSession.objects.get(id=session_id)
        session.current_level = 5
        session.difficulty_level = 5
        session.save(update_fields=['current_level', 'difficulty_level'])

        questions = self.get_questions(session_id).data
        self.answer_questions(session_id, questions, correct_count=10)

        response = self.client.post(
            reverse('game-complete-level', kwargs={'session_id': session_id})
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {'status': 'passed', 'next_level': None})
        session.refresh_from_db()
        self.user.refresh_from_db()
        self.assertEqual(session.status, 'completed')
        self.assertIsNotNone(session.ended_at)
        self.assertTrue(self.user.has_unlocked_daily_challenge)
        self.assertIsNotNone(self.user.level_5_completed_at)

    def test_requires_authentication(self):
        self.client.force_authenticate(user=None)

        response = self.client.post(reverse('game-start'))

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

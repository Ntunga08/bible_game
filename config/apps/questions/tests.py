from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.game.models import UserQuestionHistory

from .models import Category, Question


User = get_user_model()


class QuestionApiTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='StrongPass123!',
        )
        self.category = Category.objects.create(
            name='gospel',
            display_name='Gospel',
            icon='cross',
        )

    def make_question(self, **overrides):
        data = {
            'question_text': 'Where was Jesus born?',
            'options': ['Bethlehem', 'Nazareth', 'Jerusalem', 'Capernaum'],
            'correct_index': 0,
            'explanation': 'Jesus was born in Bethlehem.',
            'bible_reference': 'Matthew 2:1',
            'full_verse_text': '',
            'difficulty': 1,
            'testament': 'new',
            'category': self.category,
            'cognitive_type': 'recall',
            'topic_tags': ['birth', 'jesus'],
            'book_name': 'Matthew',
            'status': 'approved',
            'quality_score': 4.8,
            'ai_generated': False,
        }
        data.update(overrides)
        return Question.objects.create(**data)

    def admin_payload(self, **overrides):
        payload = {
            'question_text': 'Who baptized Jesus?',
            'options': ['John the Baptist', 'Peter', 'Paul', 'James'],
            'correct_index': 0,
            'explanation': 'John baptized Jesus in the Jordan River.',
            'bible_reference': 'Matthew 3:13-17',
            'full_verse_text': '',
            'difficulty': 1,
            'testament': 'new',
            'category': self.category.id,
            'cognitive_type': 'recall',
            'topic_tags': ['baptism'],
            'book_name': 'Matthew',
            'status': 'approved',
            'quality_score': 4.7,
            'ai_generated': False,
        }
        payload.update(overrides)
        return payload

    def authenticate_admin(self):
        self.client.force_authenticate(user=self.admin)

    def test_admin_can_create_question(self):
        self.authenticate_admin()

        response = self.client.post(
            reverse('question-list'),
            self.admin_payload(),
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertFalse(response.data['ai_generated'])
        self.assertTrue(
            Question.objects.filter(question_text='Who baptized Jesus?').exists()
        )

    def test_player_level_endpoint_hides_correct_index_and_serves_approved(self):
        approved = self.make_question(question_text='Approved question')
        self.make_question(question_text='Pending question', status='pending')

        response = self.client.get('/api/questions/level/1/?count=10')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], str(approved.id))
        self.assertNotIn('correct_index', response.data[0])
        self.assertNotIn('explanation', response.data[0])
        approved.refresh_from_db()
        self.assertEqual(approved.times_served, 1)

    def test_level_endpoint_accepts_count(self):
        for index in range(3):
            self.make_question(question_text=f'Question {index}')

        response = self.client.get('/api/questions/level/1/?count=2')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_authenticated_level_endpoint_avoids_recent_questions_when_possible(self):
        player = User.objects.create_user(
            username='player',
            email='player@example.com',
            password='StrongPass123!',
        )
        recent = self.make_question(question_text='Recently served')
        fresh = self.make_question(question_text='Fresh question')
        UserQuestionHistory.objects.create(user=player, question=recent)
        self.client.force_authenticate(user=player)

        response = self.client.get('/api/questions/level/1/?count=1')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]['id'], str(fresh.id))
        self.assertTrue(
            UserQuestionHistory.objects.filter(user=player, question=fresh).exists()
        )

    def test_check_answer_returns_feedback_and_updates_correct_count(self):
        question = self.make_question()

        response = self.client.post(
            reverse('question-check-answer'),
            {'question_id': str(question.id), 'selected_index': 0},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['is_correct'])
        self.assertEqual(response.data['correct_index'], 0)
        self.assertEqual(response.data['explanation'], question.explanation)
        question.refresh_from_db()
        self.assertEqual(question.times_correct, 1)
        self.assertEqual(question.times_incorrect, 0)

    def test_check_answer_updates_incorrect_count(self):
        question = self.make_question()

        response = self.client.post(
            reverse('question-check-answer'),
            {'question_id': str(question.id), 'selected_index': 2},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['is_correct'])
        question.refresh_from_db()
        self.assertEqual(question.times_correct, 0)
        self.assertEqual(question.times_incorrect, 1)

    def test_check_answer_rejects_unknown_question(self):
        response = self.client.post(
            reverse('question-check-answer'),
            {'question_id': '00000000-0000-0000-0000-000000000000', 'selected_index': 0},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('question_id', response.data)

    def test_admin_delete_archives_question(self):
        question = self.make_question()
        self.authenticate_admin()

        response = self.client.delete(
            reverse('question-detail', kwargs={'pk': question.id})
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        question.refresh_from_db()
        self.assertEqual(question.status, 'archived')

    def test_non_admin_cannot_access_full_question_list(self):
        self.make_question()

        response = self.client.get(reverse('question-list'))

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class SeedQuestionsCommandTests(APITestCase):
    def test_seed_questions_creates_categories_and_500_manual_questions(self):
        call_command('seed_questions', verbosity=0)

        self.assertEqual(Category.objects.count(), 7)
        self.assertEqual(Question.objects.count(), 500)
        self.assertEqual(Question.objects.filter(status='approved').count(), 500)
        self.assertEqual(Question.objects.filter(ai_generated=False).count(), 500)
        for level in range(1, 6):
            self.assertEqual(Question.objects.filter(difficulty=level).count(), 100)

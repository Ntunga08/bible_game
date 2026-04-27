from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import (
    AnswerResultSerializer,
    CompleteLevelSerializer,
    GameQuestionSerializer,
    GameSessionSerializer,
    StartGameSerializer,
    SubmitAnswerSerializer,
)
from .services import (
    complete_level,
    get_session_for_user,
    retry_level,
    serve_questions,
    start_game,
    submit_answer,
)


class StartGameView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        session = start_game(request.user)
        return Response(
            StartGameSerializer(session).data,
            status=status.HTTP_201_CREATED,
        )


class GameStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, session_id):
        session = get_session_for_user(session_id, request.user)
        return Response(GameSessionSerializer(session).data, status=status.HTTP_200_OK)


class GameQuestionsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, session_id):
        session = get_session_for_user(session_id, request.user)
        session_questions = serve_questions(session)
        return Response(
            GameQuestionSerializer(session_questions, many=True).data,
            status=status.HTTP_200_OK,
        )


class SubmitAnswerView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SubmitAnswerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        session = get_session_for_user(
            serializer.validated_data['session_id'],
            request.user,
        )
        session_question = submit_answer(
            session=session,
            question_id=serializer.validated_data['question_id'],
            selected_index=serializer.validated_data['selected_index'],
        )
        question = session_question.question
        result = {
            'is_correct': session_question.is_correct,
            'correct_index': question.correct_index,
            'explanation': question.explanation,
            'bible_reference': question.bible_reference,
        }
        return Response(
            AnswerResultSerializer(result).data,
            status=status.HTTP_200_OK,
        )


class CompleteLevelView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, session_id):
        session = get_session_for_user(session_id, request.user)
        result = complete_level(session)
        return Response(
            CompleteLevelSerializer(result).data,
            status=status.HTTP_200_OK,
        )


class RetryLevelView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, session_id):
        session = get_session_for_user(session_id, request.user)
        session_questions = retry_level(session)
        return Response(
            GameQuestionSerializer(session_questions, many=True).data,
            status=status.HTTP_200_OK,
        )

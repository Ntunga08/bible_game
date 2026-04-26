import uuid
from django.db import models


class Category(models.Model):
    """Biblical book categories."""

    CATEGORY_CHOICES = [
        ('law', 'Law (Torah/Pentateuch)'),
        ('history', 'History'),
        ('poetry', 'Poetry & Wisdom'),
        ('prophecy', 'Prophecy'),
        ('gospel', 'Gospel'),
        ('epistle', 'Epistle'),
        ('apocalyptic', 'Apocalyptic'),
    ]

    name = models.CharField(max_length=50, choices=CATEGORY_CHOICES, unique=True)
    display_name = models.CharField(max_length=100)
    icon = models.CharField(max_length=50, default='book')

    class Meta:
        db_table = 'categories'
        verbose_name_plural = 'categories'

    def __str__(self):
        return self.display_name


class Question(models.Model):
    """The core question model. Heart of the entire system."""

    DIFFICULTY_CHOICES = [
        (1, 'Easy'),
        (2, 'Normal'),
        (3, 'Medium'),
        (4, 'Hard'),
        (5, 'Master'),
    ]

    TESTAMENT_CHOICES = [
        ('old', 'Old Testament'),
        ('new', 'New Testament'),
        ('both', 'Both Testaments'),
    ]

    COGNITIVE_TYPE_CHOICES = [
        ('recall', 'Recall'),
        ('comprehension', 'Comprehension'),
        ('application', 'Application'),
        ('analysis', 'Analysis'),
        ('synthesis', 'Synthesis'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('archived', 'Archived'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Core content
    question_text = models.TextField()
    options = models.JSONField()           # List of 4 strings: ["A", "B", "C", "D"]
    correct_index = models.IntegerField()  # 0-3
    explanation = models.TextField()
    bible_reference = models.CharField(max_length=100)  # e.g. "John 3:16"
    full_verse_text = models.TextField(blank=True)       # cached from Bible API

    # Classification
    difficulty = models.IntegerField(choices=DIFFICULTY_CHOICES, db_index=True)
    testament = models.CharField(
        max_length=10, choices=TESTAMENT_CHOICES, db_index=True
    )
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, db_index=True
    )
    cognitive_type = models.CharField(
        max_length=20, choices=COGNITIVE_TYPE_CHOICES, db_index=True
    )
    topic_tags = models.JSONField(default=list)   # ["salvation", "faith", "miracles"]
    book_name = models.CharField(max_length=50, blank=True)  # e.g. "Romans"

    # Quality & review
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='pending', db_index=True
    )
    quality_score = models.FloatField(default=0.0)    # 1.0 - 5.0
    ai_generated = models.BooleanField(default=False)
    generation_model = models.CharField(max_length=50, blank=True)  # "claude-sonnet-4-6"
    reviewer_notes = models.TextField(blank=True)

    # Performance metadata
    times_served = models.IntegerField(default=0)
    times_correct = models.IntegerField(default=0)
    times_incorrect = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def correct_rate(self):
        total = self.times_correct + self.times_incorrect
        return (self.times_correct / total) if total > 0 else None

    class Meta:
        db_table = 'questions'
        indexes = [
            models.Index(fields=['difficulty', 'status']),
            models.Index(fields=['difficulty', 'testament', 'status']),
            models.Index(fields=['difficulty', 'category', 'status']),
        ]

    def __str__(self):
        return f"[L{self.difficulty}] {self.question_text[:60]}"

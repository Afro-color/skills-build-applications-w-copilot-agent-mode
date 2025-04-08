from django.test import TestCase
from .models import Task

class TaskModelTest(TestCase):
    def test_create_task(self):
        task = Task.objects.create(name="Test Task", completed=False)
        self.assertEqual(task.name, "Test Task")
        self.assertFalse(task.completed)

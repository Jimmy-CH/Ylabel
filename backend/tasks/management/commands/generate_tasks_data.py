
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from organizations.models import Organization  # 请根据实际路径调整
from projects.models import Project
from tasks.models import Task, Annotation, Prediction

User = get_user_model()


class Command(BaseCommand):
    help = 'Generate comprehensive test data for Label Studio-like models'

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write('Starting test data generation...')

        # 1. 创建用户
        user, created = User.objects.get_or_create(
            username='03420092',
            defaults={'email': 'annotator@example.com'}
        )
        if created:
            user.set_password('testpass123')
            user.save()
            self.stdout.write(f'Created user: {user.username}')

        # 2. 创建组织
        # org, _ = Organization.objects.get_or_create(
        #     title='Test Org',
        #     defaults={'created_by': user}
        # )
        org = user.active_organization

        # 3. 创建 Project（图像分类）
        label_config = '''
        <View>
          <Image name="image" value="$image" zoom="true" rotate="true"/>
          <Choices name="label" toName="image" choice="single">
            <Choice value="Cat" background="red"/>
            <Choice value="Dog" background="blue"/>
            <Choice value="Bird" background="green"/>
          </Choices>
        </View>
        '''.strip()

        project = Project.objects.create(
            title='Animal Image Classification',
            description='Test project for generating sample data',
            organization=org,
            created_by=user,
            label_config=label_config,
            is_published=True,
            maximum_annotations=2,
            sampling=Project.UNIFORM,
            show_skip_button=True,
            enable_empty_annotation=False,
            overlap_cohort_percentage=100,
        )
        self.stdout.write(f'✅ Created project: "{project.title}" (ID: {project.id})')

        # 4. 创建 Tasks
        task_data_list = [
            {"image": "https://example.com/cat1.jpg"},
            {"image": "https://example.com/dog1.jpg"},
            {"image": "https://example.com/bird1.jpg"},
            {"image": "https://example.com/cat2.jpg"},
        ]

        tasks = []
        for i, data in enumerate(task_data_list):
            task = Task.objects.create(
                project=project,
                data=data,
                overlap=project.maximum_annotations,
                inner_id=i + 1,
            )
            tasks.append(task)
            self.stdout.write(f'  📌 Created task {i+1}: {data["image"]}')

        # 5. 为前两个任务添加 Annotations
        annotations_to_create = [
            (tasks[0], "Cat", user),
            (tasks[0], "Cat", None),  # 第二个标注者（模拟多人）
            (tasks[1], "Dog", user),
        ]

        for task, label_value, annotator in annotations_to_create:
            ann = Annotation.objects.create(
                project=project,
                task=task,
                result=[
                    {
                        "from_name": "label",
                        "to_name": "image",
                        "type": "choices",
                        "value": {"choices": [label_value]}
                    }
                ],
                completed_by=annotator or user,
                was_cancelled=False,
                ground_truth=(label_value == "Cat"),  # 示例：把 Cat 当作 ground truth
            )
            self.stdout.write(f'  ✍️ Added annotation: {label_value} on task {task.id}')

        # 6. 添加 Predictions
        predictions_to_create = [
            (tasks[2], "Bird", 0.92),
            (tasks[3], "Cat", 0.87),
        ]

        for task, pred_label, score in predictions_to_create:
            Prediction.objects.create(
                project=project,
                task=task,
                result=[
                    {
                        "from_name": "label",
                        "to_name": "image",
                        "type": "choices",
                        "value": {"choices": [pred_label]}
                    }
                ],
                score=score,
                model_version="v1-test-model",
            )
            self.stdout.write(f'  🤖 Added prediction: {pred_label} (score={score}) on task {task.id}')

        # 7. 更新项目统计（可选，如果模型支持）
        if hasattr(project, 'update_tasks_states'):
            project.update_tasks_states(
                maximum_annotations_changed=False,
                overlap_cohort_percentage_changed=False,
                tasks_number_changed=True,
            )

        self.stdout.write(
            self.style.SUCCESS(
                f'\n🎉 Successfully generated test data!\n'
                f'- Project: {project.title}\n'
                f'- Tasks: {len(tasks)}\n'
                f'- Annotations: {len(annotations_to_create)}\n'
                f'- Predictions: {len(predictions_to_create)}'
            )
        )

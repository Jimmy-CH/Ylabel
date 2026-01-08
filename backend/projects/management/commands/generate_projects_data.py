# projects/management/commands/generate_projects_data.py
import json
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from organizations.models import Organization  # 假设你有这个模型
from projects.models import Project
from tasks.models import Task, Annotation
from django.conf import settings

User = get_user_model()


class Command(BaseCommand):
    help = 'Generate test data for Project model'

    def handle(self, *args, **options):
        # 1. 创建测试用户
        user, created = User.objects.get_or_create(
            username='testuser',
            defaults={
                'email': 'testuser@example.com',
                'is_active': True,
            }
        )
        if created:
            user.set_password('password123')
            user.save()
            self.stdout.write(f'Created user: {user.username}')

        # 2. 创建组织（Organization）
        org, _ = Organization.objects.get_or_create(
            title='Test Organization',
            defaults={'created_by': user}
        )

        # 3. 设置一个典型的 label_config（图像分类示例）
        label_config = '''
        <View>
          <Image name="image" value="$image"/>
          <Choices name="choice" toName="image">
            <Choice value="Cat"/>
            <Choice value="Dog"/>
            <Choice value="Bird"/>
          </Choices>
        </View>
        '''

        # 4. 创建 Project
        project = Project.objects.create(
            title='Test Image Classification Project',
            description='A sample project for testing',
            organization=org,
            created_by=user,
            label_config=label_config.strip(),
            is_published=True,
            maximum_annotations=2,
            sampling=Project.UNIFORM,
            show_skip_button=True,
            enable_empty_annotation=False,
        )
        self.stdout.write(f'Created project: {project.title} (ID: {project.id})')

        # 5. （可选）创建几个测试任务
        sample_tasks = [
            {"image": "https://example.com/cat1.jpg"},
            {"image": "https://example.com/dog1.jpg"},
            {"image": "https://example.com/bird1.jpg"},
        ]

        for i, data in enumerate(sample_tasks):
            task = Task.objects.create(
                project=project,
                data=data,
                overlap=project.maximum_annotations,
            )
            self.stdout.write(f'  - Created task {i+1}: {data["image"]}')

            # 可选：为第一个任务添加一个模拟标注
            if i == 0:
                Annotation.objects.create(
                    project=project,
                    task=task,
                    result=[
                        {
                            "from_name": "choice",
                            "to_name": "image",
                            "type": "choices",
                            "value": {"choices": ["Cat"]}
                        }
                    ],
                    completed_by=user,
                )
                self.stdout.write(f'    - Added sample annotation to task {i+1}')

        self.stdout.write(
            self.style.SUCCESS('Successfully generated test project and data!')
        )


# Generated by Django 4.2.21 on 2025-06-08 18:10

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_patientprofile_image'),
    ]

    operations = [
        migrations.CreateModel(
            name='DoctorReview',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rating', models.PositiveIntegerField()),
                ('comment', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('doctor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reviews', to='core.doctorprofile')),
                ('patient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reviews', to='core.patientprofile')),
            ],
        ),
    ]

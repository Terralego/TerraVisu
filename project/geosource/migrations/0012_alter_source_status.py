# Generated by Django 4.1.13 on 2023-11-20 15:16

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("geosource", "0011_sourcereporting_source_status_alter_source_report"),
    ]

    operations = [
        migrations.AlterField(
            model_name="source",
            name="status",
            field=models.PositiveSmallIntegerField(
                choices=[
                    (0, "Need sync"),
                    (1, "Pending"),
                    (2, "Done"),
                    (3, "In progress"),
                ],
                default=0,
            ),
        ),
    ]

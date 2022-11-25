# Generated by Django 4.1.3 on 2022-11-25 09:35

from django.db import migrations, models

import project.geosource.models


class Migration(migrations.Migration):

    dependencies = [
        ("geosource", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="field",
            name="data_type",
            field=models.IntegerField(
                choices=[
                    (1, project.geosource.models.FieldTypes["String"]),
                    (2, project.geosource.models.FieldTypes["Integer"]),
                    (3, project.geosource.models.FieldTypes["Float"]),
                    (4, project.geosource.models.FieldTypes["Boolean"]),
                    (5, project.geosource.models.FieldTypes["Undefined"]),
                    (6, project.geosource.models.FieldTypes["Date"]),
                ],
                default=project.geosource.models.FieldTypes["Undefined"],
            ),
        ),
    ]

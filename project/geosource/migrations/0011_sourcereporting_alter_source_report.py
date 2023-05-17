# Generated by Django 4.1.8 on 2023-05-16 14:37

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("geosource", "0010_auto_20230414_0747"),
    ]

    operations = [
        migrations.CreateModel(
            name="SourceReporting",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[("0", "Success"), ("1", "Error"), ("2", "Warning")],
                        max_length=10,
                        null=True,
                    ),
                ),
                ("message", models.CharField(default="", max_length=255)),
                ("started", models.DateTimeField(null=True)),
                ("ended", models.DateTimeField(null=True)),
                ("added_lines", models.PositiveIntegerField(default=0)),
                ("deleted_lines", models.PositiveIntegerField(default=0)),
                ("modified_lines", models.PositiveIntegerField(default=0)),
                ("errors", models.JSONField(default=list)),
            ],
        ),
        migrations.AlterField(
            model_name="source",
            name="report",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to="geosource.sourcereporting",
            ),
        ),
    ]

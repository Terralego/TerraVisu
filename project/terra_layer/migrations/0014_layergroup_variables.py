# Generated by Django 4.1.13 on 2023-12-18 17:51

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("terra_layer", "0013_layergroup_byvariable"),
    ]

    operations = [
        migrations.AddField(
            model_name="layergroup",
            name="variables",
            field=models.JSONField(default=list),
        ),
    ]

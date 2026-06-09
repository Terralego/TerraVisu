from django.db import migrations

class Migration(migrations.Migration):
    initial = True
    dependencies = []

    operations = [
        migrations.RunSQL(
            sql="CREATE EXTENSION IF NOT EXISTS unaccent;",
            reverse_sql="",
            # reverse_sql="DROP EXTENSION unaccent;",
        ),
    ]
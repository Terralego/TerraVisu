from django.db import migrations


class Migration(migrations.Migration):
    initial = True
    dependencies = []

    operations = [
        migrations.RunSQL(
            sql="CREATE EXTENSION IF NOT EXISTS unaccent;",
            # pas de DROP EXTENSION au retour : d'autres apps peuvent l'utiliser
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('terra_layer', '0026_install_jenks_bins'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
DROP FUNCTION IF EXISTS terra_jenks_bins;
DROP FUNCTION IF EXISTS terra_jenks_bins_iteration;
""",
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]

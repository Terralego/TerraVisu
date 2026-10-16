from django.db import migrations


def forward(apps, schema_editor):
    ContentType = apps.get_model("contenttypes", "ContentType")
    db_alias = schema_editor.connection.alias

    geofile_ct, _ = ContentType.objects.using(db_alias).get_or_create(
        app_label="geosource",
        model="geofilesource",
    )

    with schema_editor.connection.cursor() as cursor:
        cursor.execute("DROP TABLE IF EXISTS geosource_geopackagesource CASCADE;")

        cursor.execute("""
            INSERT INTO geosource_geofilesource (source_ptr_id, file, layer_name)
            SELECT source_ptr_id, file, ''
            FROM geosource_geojsonsource
            ON CONFLICT (source_ptr_id) DO NOTHING;
        """)

        cursor.execute("""
            INSERT INTO geosource_geofilesource (source_ptr_id, file, layer_name)
            SELECT source_ptr_id, file, ''
            FROM geosource_shapefilesource
            ON CONFLICT (source_ptr_id) DO NOTHING;
        """)

        cursor.execute(
            """
            UPDATE geosource_source
            SET polymorphic_ctype_id = %s
            WHERE id IN (SELECT source_ptr_id FROM geosource_geofilesource);
        """,
            [geofile_ct.id],
        )

    ContentType.objects.using(db_alias).filter(
        app_label="geosource",
        model__in=["geojsonsource", "shapefilesource", "geopackagesource"],
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("contenttypes", "0002_remove_content_type_name"),
        ("geosource", "0019_geofilesource"),
    ]

    operations = [
        migrations.RunPython(forward, migrations.RunPython.noop),
        migrations.DeleteModel(
            name="GeoJSONSource",
        ),
        migrations.DeleteModel(
            name="ShapefileSource",
        ),
    ]

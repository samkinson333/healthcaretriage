from django.db import migrations

TABLE_NAME = 'triage_triageassessment'
LEGACY_COLUMNS = ('assigned_at', 'assigned_role', 'assigned_to')


def _existing_columns(schema_editor):
    with schema_editor.connection.cursor() as cursor:
        description = schema_editor.connection.introspection.get_table_description(
            cursor, TABLE_NAME
        )
    return {column.name for column in description}


def drop_legacy_columns(apps, schema_editor):
    """Remove assignment columns left over from an earlier model revision.

    Assignment state is now stored inside the assessment ``inputs`` JSON, so
    these columns are unused. They are dropped only when present, which keeps
    this migration safe to replay on a freshly created database.
    """
    existing = _existing_columns(schema_editor)
    quote = schema_editor.connection.ops.quote_name
    for column in LEGACY_COLUMNS:
        if column in existing:
            schema_editor.execute(
                f'ALTER TABLE {quote(TABLE_NAME)} DROP COLUMN {quote(column)}'
            )


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('triage', '0002_triageassessment_queueevent_and_more'),
    ]

    operations = [
        migrations.RunPython(drop_legacy_columns, noop),
    ]

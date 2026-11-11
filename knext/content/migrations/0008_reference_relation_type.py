from django.db import migrations


def seed_reference(apps, schema_editor):
    apps.get_model("content", "RelationType").objects.using(schema_editor.connection.alias).get_or_create(
        key="reference",
        defaults={
            "label": "Verweis",
            "description": "Verweist auf eine verwandte Ressource, ohne Zustimmung, Reihenfolge oder Abhängigkeit zu behaupten.",
        },
    )


class Migration(migrations.Migration):
    dependencies = [("content", "0007_contentresource_relationtype_collectionentry_and_more")]
    operations = [migrations.RunPython(seed_reference, migrations.RunPython.noop)]

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("content", "0008_reference_relation_type")]

    operations = [
        migrations.AddField(
            model_name="relationtype",
            name="catalog_managed",
            field=models.BooleanField(default=False, editable=False),
        ),
    ]

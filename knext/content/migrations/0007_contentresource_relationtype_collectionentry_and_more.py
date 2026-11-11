import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0006_filesystemartifact_importbatch_importjob_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ContentResource',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('kind', models.CharField(choices=[('document', 'Dokument'), ('block', 'Block'), ('folder', 'Ordner'), ('collection', 'Zusammenstellung')], max_length=20)),
                ('domain', models.CharField(db_index=True, max_length=150)),
                ('title', models.CharField(max_length=255)),
                ('local_key', models.CharField(blank=True, max_length=300)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('document', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='resources', to='content.contentdocument')),
            ],
            options={
                'ordering': ['title', 'id'],
            },
        ),
        migrations.CreateModel(
            name='RelationType',
            fields=[
                ('key', models.SlugField(max_length=80, primary_key=True, serialize=False)),
                ('label', models.CharField(max_length=150)),
                ('description', models.TextField(verbose_name='Definition und Begründung')),
            ],
        ),
        migrations.CreateModel(
            name='CollectionEntry',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('key', models.SlugField(max_length=100)),
                ('position', models.PositiveIntegerField(default=0)),
                ('parent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='children', to='content.collectionentry')),
                ('revision', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='content.contentrevision')),
                ('resource', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='placements', to='content.contentresource')),
            ],
            options={
                'ordering': ['position', 'key'],
            },
        ),
        migrations.CreateModel(
            name='BlockSnapshot',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('explicit_id', models.CharField(blank=True, max_length=255)),
                ('level', models.PositiveSmallIntegerField()),
                ('start_line', models.PositiveIntegerField()),
                ('end_line', models.PositiveIntegerField()),
                ('body', models.TextField()),
                ('revision', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='blocks', to='content.contentrevision')),
                ('resource', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='snapshots', to='content.contentresource')),
            ],
            options={
                'ordering': ['start_line'],
            },
        ),
        migrations.CreateModel(
            name='ResourceRelation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reason', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
                ('relation_type', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='content.relationtype')),
                ('source', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='outgoing_relations', to='content.contentresource')),
                ('target', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='incoming_relations', to='content.contentresource')),
            ],
        ),
        migrations.CreateModel(
            name='ContentCollection',
            fields=[
                ('resource', models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, primary_key=True, related_name='collection', serialize=False, to='content.contentresource')),
                ('kind', models.CharField(choices=[('sequence', 'Sequenz'), ('hierarchy', 'Hierarchie'), ('set', 'Sammlung'), ('network', 'Netz')], default='hierarchy', max_length=20)),
                ('description', models.TextField(blank=True)),
                ('version', models.PositiveIntegerField(default=1)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
                ('source_revision', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='outline', to='content.contentrevision')),
            ],
            options={
                'ordering': ['-updated_at'],
            },
        ),
        migrations.CreateModel(
            name='CollectionLink',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reason', models.TextField(blank=True)),
                ('source', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='outgoing_links', to='content.collectionentry')),
                ('target', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='incoming_links', to='content.collectionentry')),
                ('relation_type', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='content.relationtype')),
                ('collection', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='links', to='content.contentcollection')),
            ],
        ),
        migrations.AddField(
            model_name='collectionentry',
            name='collection',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='entries', to='content.contentcollection'),
        ),
        migrations.AddConstraint(
            model_name='contentresource',
            constraint=models.UniqueConstraint(condition=models.Q(('document__isnull', False)), fields=('document', 'local_key'), name='unique_document_resource_key'),
        ),
        migrations.AddConstraint(
            model_name='contentresource',
            constraint=models.CheckConstraint(condition=models.Q(models.Q(('document__isnull', False), ('kind', 'document'), ('local_key', '')), models.Q(('document__isnull', False), ('kind', 'block'), models.Q(('local_key', ''), _negated=True)), models.Q(('document__isnull', True), ('kind__in', ['folder', 'collection']), ('local_key', '')), _connector='OR'), name='resource_identity_matches_kind'),
        ),
        migrations.AddConstraint(
            model_name='blocksnapshot',
            constraint=models.UniqueConstraint(fields=('resource', 'revision'), name='unique_block_revision'),
        ),
        migrations.AddConstraint(
            model_name='blocksnapshot',
            constraint=models.CheckConstraint(condition=models.Q(('level__gte', 1), ('level__lte', 6), ('start_line__gte', 1), ('end_line__gte', models.F('start_line'))), name='valid_block_source_span'),
        ),
        migrations.AddConstraint(
            model_name='resourcerelation',
            constraint=models.UniqueConstraint(fields=('source', 'target', 'relation_type'), name='unique_resource_relation'),
        ),
        migrations.AddConstraint(
            model_name='collectionlink',
            constraint=models.UniqueConstraint(fields=('source', 'target', 'relation_type'), name='unique_collection_link'),
        ),
        migrations.AddConstraint(
            model_name='collectionentry',
            constraint=models.UniqueConstraint(fields=('collection', 'key'), name='unique_collection_entry_key'),
        ),
    ]

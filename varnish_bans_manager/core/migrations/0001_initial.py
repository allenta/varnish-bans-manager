# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import varnish_bans_manager.filesystem.models
import django.utils.timezone
import varnish_bans_manager.core.models.user_profile
import django.db.models.deletion
from django.conf import settings
import varnish_bans_manager.core.models.base


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0001_initial'),
        ('contenttypes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(default=django.utils.timezone.now, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('first_name', models.CharField(max_length=30, verbose_name='first name', blank=True)),
                ('last_name', models.CharField(max_length=30, verbose_name='last name', blank=True)),
                ('email', models.EmailField(unique=True, max_length=75, verbose_name='email address')),
                ('is_staff', models.BooleanField(default=False, verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
            ],
            options={
                'verbose_name': 'user',
                'verbose_name_plural': 'users',
                'permissions': (('can_access_advanced_ban_submission', 'Access advanced ban submission form'), ('can_access_expert_ban_submission', 'Access expert ban submission form'), ('can_access_bans_submissions', 'Access bans submissions'), ('can_access_bans_status', 'Access bans status'), ('can_access_caches_management', 'Access caches management'), ('can_access_users_management', 'Access users management'), ('can_access_settings', 'Access settings')),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='BanSubmission',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('launched_at', models.DateTimeField()),
                ('ban_type', models.PositiveSmallIntegerField(choices=[(1, 'basic'), (2, 'advanced'), (3, 'expert')])),
                ('expression', models.CharField(max_length=2048)),
                ('target_id', models.PositiveIntegerField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('target_content_type', models.ForeignKey(to='contenttypes.ContentType')),
                ('user', models.ForeignKey(related_name='ban_submissions', to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='BanSubmissionItem',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('success', models.BooleanField(default=False)),
                ('message', models.CharField(max_length=1024, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('ban_submission', models.ForeignKey(related_name='items', to='core.BanSubmission')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Group',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(help_text='Some name used internally by VBM to refer to the group of caching nodes.', max_length=255, verbose_name='Name')),
                ('weight', models.SmallIntegerField(default=0)),
                ('revision', varnish_bans_manager.core.models.base.RevisionField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'cache group',
                'verbose_name_plural': 'cache groups',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Node',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(help_text='Some name used internally by VBM to refer to the cache node. If not provided, the host and port number of the node will be used.', max_length=255, null=True, verbose_name='Name', blank=True)),
                ('host', models.CharField(help_text='Name or IP address of the server running the Varnish cache node.', max_length=255, verbose_name='Host')),
                ('port', models.PositiveIntegerField(help_text='Varnish management port number.', verbose_name='Port')),
                ('secret', models.TextField(help_text='If the -S secret-file is used in the cache node, provide here the contents of that file in order to authenticate CLI connections opened by VBM.', max_length=65536, null=True, verbose_name='Secret', blank=True)),
                ('version', models.SmallIntegerField(default=30, help_text='Select the Varnish version running in the cache node.', verbose_name='Version', choices=[(21, b'2.1'), (30, b'>= 3.0')])),
                ('weight', models.SmallIntegerField(default=0)),
                ('revision', varnish_bans_manager.core.models.base.RevisionField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('group', models.ForeignKey(related_name='nodes', on_delete=django.db.models.deletion.SET_NULL, blank=True, to='core.Group', null=True)),
            ],
            options={
                'verbose_name': 'cache node',
                'verbose_name_plural': 'cache nodes',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Setting',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=255, db_index=True)),
                ('value', varnish_bans_manager.core.models.base.JSONField(max_length=1024)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('photo', varnish_bans_manager.filesystem.models.ImageField(contents_generator=None, max_upload_size=1048576, path_generator=None, max_width=128, strong_caching=True, upload_to=varnish_bans_manager.core.models.user_profile._photo_upload_destination, private=True, content_types=[b'image/jpeg', b'image/png'], attachment_filename=varnish_bans_manager.filesystem.models._default_attachment_filename, max_height=128, attachment=False, blank=True, help_text='Upload a photo. It will only be visible by administrators.', null=True, verbose_name='Photo', condition=varnish_bans_manager.filesystem.models._default_condition)),
                ('revision', varnish_bans_manager.core.models.base.RevisionField(default=0)),
                ('creator', models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, null=True)),
                ('user', models.OneToOneField(related_name='profile', to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='bansubmissionitem',
            name='node',
            field=models.ForeignKey(related_name='ban_submission_items', to='core.Node'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='user',
            name='groups',
            field=models.ManyToManyField(related_query_name='user', related_name='user_set', to='auth.Group', blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of his/her group.', verbose_name='groups'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='user',
            name='user_permissions',
            field=models.ManyToManyField(related_query_name='user', related_name='user_set', to='auth.Permission', blank=True, help_text='Specific permissions for this user.', verbose_name='user permissions'),
            preserve_default=True,
        ),
    ]

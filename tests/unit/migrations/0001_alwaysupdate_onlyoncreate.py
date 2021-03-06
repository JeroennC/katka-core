# Generated by Django 2.1.5 on 2019-02-18 01:38

from django.db import migrations, models

import katka.fields


class Migration(migrations.Migration):

    initial = True

    operations = [
        migrations.CreateModel(
            name="AlwaysUpdate",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("field", katka.fields.AutoUsernameField(max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name="OnlyOnCreate",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("field", katka.fields.AutoUsernameField(max_length=50)),
            ],
        ),
    ]

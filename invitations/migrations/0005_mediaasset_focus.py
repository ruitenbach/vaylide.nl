from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("invitations", "0004_alter_mediaasset_kind")]

    operations = [
        migrations.AddField(model_name="mediaasset", name="focus_x", field=models.PositiveSmallIntegerField(blank=True, null=True)),
        migrations.AddField(model_name="mediaasset", name="focus_y", field=models.PositiveSmallIntegerField(blank=True, null=True)),
        migrations.AddField(model_name="mediaasset", name="faces", field=models.PositiveSmallIntegerField(blank=True, null=True)),
    ]

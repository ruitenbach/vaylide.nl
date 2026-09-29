from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("invitations", "0005_mediaasset_focus")]

    operations = [
        migrations.AddField(model_name="invitation", name="package_code",
                            field=models.CharField(blank=True, max_length=40, verbose_name="gekozen pakket")),
    ]

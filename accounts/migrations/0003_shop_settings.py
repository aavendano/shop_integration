# Generated migration for Shop settings fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_shop_is_authentified'),
    ]

    operations = [
        migrations.AddField(
            model_name='shop',
            name='pricing_config_enabled',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='shop',
            name='auto_sync_enabled',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='shop',
            name='sync_frequency',
            field=models.CharField(
                choices=[
                    ('hourly', 'Hourly'),
                    ('daily', 'Daily'),
                    ('weekly', 'Weekly'),
                    ('manual', 'Manual'),
                ],
                default='daily',
                max_length=20
            ),
        ),
    ]

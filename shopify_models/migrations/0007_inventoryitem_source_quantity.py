from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("shopify_models", "0006_rename_sku_inventoryitem_shopify_sku"),
    ]

    operations = [
        migrations.AddField(
            model_name="inventoryitem",
            name="source_quantity",
            field=models.IntegerField(null=True),
        ),
    ]
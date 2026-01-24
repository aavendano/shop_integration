from django.apps import AppConfig


class ShopifyWebhookConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'shopify_webhook'
    verbose_name = 'Shopify Webhook'

    def ready(self):
        """
        Import signals when the app is ready.
        This ensures that signal handlers are registered.
        """
        import shopify_webhook.signals  # noqa

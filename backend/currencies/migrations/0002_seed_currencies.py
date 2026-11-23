"""Load the initial ISO 4217 currencies.

The data lives here, frozen in time, on purpose: a migration must produce the
same result whenever it runs, even if the app code changes later. To add or
change currencies in the future, create a new migration.
"""

from django.db import migrations

# (code, name, decimal_places) from the ISO 4217 standard.
CURRENCIES = [
    ("BRL", "Brazilian Real", 2),
    ("CAD", "Canadian Dollar", 2),
    ("COP", "Colombian Peso", 2),
    ("CRC", "Costa Rican Colon", 2),
    ("EUR", "Euro", 2),
    ("GBP", "Pound Sterling", 2),
    ("JPY", "Yen", 0),
    ("MXN", "Mexican Peso", 2),
    ("USD", "US Dollar", 2),
]


def seed_currencies(apps, schema_editor):
    # Historical model: the Currency as it was at THIS migration, not today's code.
    Currency = apps.get_model("currencies", "Currency")
    for code, name, decimal_places in CURRENCIES:
        Currency.objects.update_or_create(
            code=code,
            defaults={"name": name, "decimal_places": decimal_places, "is_active": True},
        )


def remove_currencies(apps, schema_editor):
    Currency = apps.get_model("currencies", "Currency")
    Currency.objects.filter(code__in=[code for code, _, _ in CURRENCIES]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("currencies", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_currencies, reverse_code=remove_currencies),
    ]

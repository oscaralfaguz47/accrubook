from django.core.validators import MaxValueValidator, RegexValidator
from django.db import models

ISO_4217_CODE_REGEX = r"^[A-Z]{3}$"
MAX_DECIMAL_PLACES = 4


class Currency(models.Model):
    """A currency from the ISO 4217 standard (e.g. USD, CRC, EUR).

    Global reference data: shared by all tenants and loaded through migrations,
    not created by users.
    """

    code = models.CharField(
        primary_key=True,
        max_length=3,
        validators=[RegexValidator(ISO_4217_CODE_REGEX, "Use a 3-letter uppercase ISO 4217 code.")],
        help_text="ISO 4217 alphabetic code, e.g. USD.",
    )
    name = models.CharField(max_length=100, help_text="English name, e.g. US Dollar.")
    decimal_places = models.PositiveSmallIntegerField(
        validators=[MaxValueValidator(MAX_DECIMAL_PLACES)],
        help_text="Digits after the decimal point: 2 for USD, 0 for JPY, 3 for KWD.",
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Retired currencies are deactivated, never deleted.",
    )

    class Meta:
        ordering = ["code"]
        verbose_name_plural = "currencies"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(code__regex=ISO_4217_CODE_REGEX),
                name="currency_code_iso_4217_format",
            ),
            models.CheckConstraint(
                condition=models.Q(decimal_places__lte=MAX_DECIMAL_PLACES),
                name="currency_decimal_places_lte_4",
            ),
        ]

    def __str__(self) -> str:
        return self.code

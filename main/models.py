from django.db import models
from django.utils.text import slugify
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.utils import timezone
from django.db.models import Q


class User(AbstractUser):
    pass


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name


class Lot(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Активен"
        CLOSED = "closed", "Завершен"
        CANCELLED = "cancelled", "Отменен"

    title = models.CharField(max_length=200)
    description = models.TextField()
    condition = models.CharField(
        max_length=20,
        choices=[("new", "Новый"), ("used", "Б/У"), ("refurbished", "восстановленный")],
        default="new",
    )
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True, related_name="lots"
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="owner_lots"
    )

    start_price = models.DecimalField(max_digits=10, decimal_places=2)
    current_price = models.DecimalField(max_digits=10, decimal_places=2)
    min_bid_step = models.DecimalField(max_digits=10, decimal_places=2, default=1.00)

    start_time = models.DateTimeField(default=timezone.now)
    end_time = models.DateTimeField()

    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.ACTIVE
    )

    winner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="won_lots",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def is_expired(self):
        return timezone.now() > self.end_time

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "end_time"]),
        ]

    def __str__(self):
        return self.title


class Bid(models.Model):
    lot = models.ForeignKey(Lot, on_delete=models.CASCADE, related_name="bids")

    bidder = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="bids"
    )

    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["lot", "-amount"])]

    def __str__(self):
        return f"{self.bidder} - {self.amount} на {self.lot}"


class LotImage(models.Model):
    lot = models.ForeignKey(Lot, on_delete=models.CASCADE, related_name="images")

    image = models.ImageField(upload_to="lots/")
    is_main = models.BooleanField(default=False, verbose_name="Главное фото")

    class Meta:
        models.UniqueConstraint(
            fields=["lot"], condition=Q(is_main=True), name="unique_main_image_per_lot"
        )

    def __str__(self):
        return f"Фото для {self.lot.title}"


class Notification(models.Model):
    class Type(models.TextChoices):
        OUTBID = "outbid", "Ставка перебита"
        WON = "won", "Аукцион выигран"
        LOST = "lost", "Аукцион проигран"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications"
    )

    notification_type = models.CharField(max_length=20, choices=Type.choices)
    lot = models.ForeignKey(Lot, on_delete=models.CASCADE, null=True, blank=True)

    message = models.CharField(max_length=225)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Уведомление для {self.user.username}: {self.message}"

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from main.models import Lot, Bid


class Command(BaseCommand):
    help = "Закрывает аукционы, у которых истекло время, и определяет победителя"

    def handle(self, *args, **kwargs):
        expired_lots = Lot.objects.filter(
            status=Lot.Status.ACTIVE, end_time__lt=timezone.now()
        )

        closed_count = 0

        for lot in expired_lots:
            with transaction.atomic():
                winning_bid = lot.bids.order_by("-amount").first()

                if winning_bid:
                    lot.winner = winning_bid.bidder
                else:
                    lot.winner = None

                lot.status = Lot.Status.CLOSED
                lot.save()
                closed_count += 1

        self.stdout.write(
            self.style.SUCCESS(f"Успешно закрыто аукционов: {closed_count}")
        )

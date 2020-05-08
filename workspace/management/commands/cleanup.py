from django.core.management.base import BaseCommand, CommandError
from workspace.models import Notification, AttendanceToken
from workspace.views import TZ_TARGET
from datetime import datetime


class Command(BaseCommand):
    help = 'Cleans up temporary objects that got left without purpose for some reason'

    def handle(self, *args, **options):
        notif = Notification.objects.all()
        k = 0
        p = 0
        warn = False
        for n in notif:
            if n.expire < TZ_TARGET.localize(datetime.now()) or n.user.count() == 0:
                n.delete()
                k += 1
        tokens = AttendanceToken.objects.all()
        for at in tokens:
            if at.expire < TZ_TARGET.localize(datetime.now()):
                at.delete()
        self.stdout.write(self.style.SUCCESS(
            'Successfully cleaned {} notifications and {} expired attendance tokens'.format(k, p)))

from django.core.management.base import BaseCommand

from apps.daily.services import create_today_challenge_if_missing


class Command(BaseCommand):
    help = 'Generate today\'s hard/master daily challenge if it does not exist.'

    def handle(self, *args, **options):
        challenge, created = create_today_challenge_if_missing()
        if created:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Created daily challenge {challenge.title} ({challenge.id}).'
                )
            )
            return

        self.stdout.write(
            self.style.WARNING(
                f'Daily challenge already exists for {challenge.date}; doing nothing.'
            )
        )

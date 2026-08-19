import re

import openpyxl
from django.core.management.base import BaseCommand, CommandError

from voting.models import Student

REG_NUMBER_RE = re.compile(r'^\d{6,}$')


class Command(BaseCommand):
    help = (
        "Import the official BME class list (xlsx) as the approved voter roster. "
        "Safe to re-run: existing students are only updated (name), never have "
        "their password touched. New students are created with an unusable "
        "password so they must self-register (Reg Number + Password) before "
        "they can log in."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            'file_path',
            nargs='?',
            default='BME Class List Corrected-1.xlsx',
            help='Path to the roster .xlsx file (default: BME Class List Corrected-1.xlsx in the project root)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Parse and report counts without writing to the database.',
        )

    def handle(self, *args, **options):
        file_path = options['file_path']
        dry_run = options['dry_run']

        try:
            workbook = openpyxl.load_workbook(file_path, data_only=False)
        except FileNotFoundError:
            raise CommandError(f"Roster file not found: {file_path}")

        sheet = workbook.active
        roster = {}  # reg_number -> full_name

        for row in sheet.iter_rows(values_only=True):
            name, reg = row[1], row[2]
            if reg is None or name is None:
                continue

            if isinstance(reg, str):
                reg = reg.strip()
                if not REG_NUMBER_RE.match(reg):
                    continue
            else:
                try:
                    reg = str(int(reg))
                except (TypeError, ValueError):
                    continue

            if not isinstance(name, str) or not name.strip():
                continue
            name = name.strip()
            if name.upper() in ('NAMES', 'NAME'):
                continue

            roster[reg] = name

        created, updated, unchanged = 0, 0, 0

        for reg_number, full_name in roster.items():
            student = Student.objects.filter(reg_number=reg_number).first()
            if student is None:
                created += 1
                if not dry_run:
                    student = Student(reg_number=reg_number, full_name=full_name)
                    student.set_unusable_password()
                    student.save()
            elif student.full_name != full_name:
                updated += 1
                if not dry_run:
                    student.full_name = full_name
                    student.save(update_fields=['full_name'])
            else:
                unchanged += 1

        prefix = '[DRY RUN] ' if dry_run else ''
        self.stdout.write(self.style.SUCCESS(
            f"{prefix}Roster parsed: {len(roster)} unique students. "
            f"Created: {created}, updated: {updated}, unchanged: {unchanged}."
        ))

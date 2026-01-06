import os
import shutil
from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Backup database and server files'

    def add_arguments(self, parser):
        parser.add_argument(
            '--backup-dir',
            type=str,
            default='backups',
            help='Directory to store backups',
        )

    def handle(self, *args, **options):
        backup_dir = Path(settings.BASE_DIR) / options['backup_dir']
        backup_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Backup database
        db_path = Path(settings.DATABASES['default']['NAME'])
        if db_path.exists():
            db_backup = backup_dir / f"db_{timestamp}.sqlite3"
            shutil.copy2(db_path, db_backup)
            self.stdout.write(f"Database backed up to {db_backup}")

        # Backup server files
        server_dir = Path(settings.MINECRAFT_DIR)
        if server_dir.exists():
            server_backup = backup_dir / f"servers_{timestamp}"
            shutil.copytree(server_dir, server_backup, dirs_exist_ok=True)
            self.stdout.write(f"Server files backed up to {server_backup}")

        self.stdout.write(self.style.SUCCESS('Backup completed successfully'))
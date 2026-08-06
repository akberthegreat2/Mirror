"""Management command to create Mirror users with appropriate groups."""

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from mirror_control_panel.permissions import setup_groups

User = get_user_model()


class Command(BaseCommand):
    """Create a Mirror user with specified role."""

    help = "Create a Mirror user with specified role (Viewer, Operator, Admin)"

    def add_arguments(self, parser) -> None:
        """Add command arguments."""
        parser.add_argument(
            "username",
            type=str,
            help="Username for the new user",
        )
        parser.add_argument(
            "--email",
            type=str,
            help="Email address for the user",
        )
        parser.add_argument(
            "--password",
            type=str,
            help="Password for the user (if not provided, will prompt)",
        )
        parser.add_argument(
            "--role",
            type=str,
            choices=["Viewer", "Operator", "Admin"],
            default="Operator",
            help="Role for the user (default: Operator)",
        )
        parser.add_argument(
            "--superuser",
            action="store_true",
            help="Create as superuser (overrides --role)",
        )

    def handle(self, *args, **options) -> None:
        """Handle the command."""
        username = options["username"]
        email = options.get("email", "")
        password = options.get("password")
        role = options["role"]
        is_superuser = options["superuser"]

        # Check if user exists
        if User.objects.filter(username=username).exists():
            raise CommandError(f"User '{username}' already exists")

        # Ensure groups exist
        setup_groups()

        # Create user
        with transaction.atomic():
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                is_superuser=is_superuser,
                is_staff=True,  # Staff access for admin
            )

            # Add to group if not superuser
            if not is_superuser:
                group, _ = Group.objects.get_or_create(name=role)
                user.groups.add(group)
                user.save()

        # Output success message
        self.stdout.write(
            self.style.SUCCESS(f"Successfully created user '{username}' with role '{role}'")
        )

        if not password:
            self.stdout.write(
                self.style.WARNING(
                    "Password was not set. Use 'manage.py changepassword' to set one."
                )
            )

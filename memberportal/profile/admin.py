from django.contrib import admin
from .models import *
from import_export.admin import ImportExportModelAdmin
from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget
from django.utils import timezone


class UserResource(resources.ModelResource):
    first_name = fields.Field(
        column_name="first_name",
        attribute="first_name",
        widget=ForeignKeyWidget(Profile, "first_name"),
    )
    last_name = fields.Field(
        column_name="last_name",
        attribute="last_name",
        widget=ForeignKeyWidget(Profile, "last_name"),
    )
    screen_name = fields.Field(
        column_name="screen_name",
        attribute="screen_name",
        widget=ForeignKeyWidget(Profile, "screen_name"),
    )
    rfid = fields.Field(
        column_name="rfid", attribute="rfid", widget=ForeignKeyWidget(Profile, "rfid")
    )
    state = fields.Field(
        column_name="state",
        attribute="state",
        widget=ForeignKeyWidget(Profile, "state"),
    )
    stripe_customer_id = fields.Field(
        column_name="stripe_customer_id",
        attribute="stripe_customer_id",
        widget=ForeignKeyWidget(Profile, "stripe_customer_id"),
    )
    stripe_card_expiry = fields.Field(
        column_name="stripe_card_expiry",
        attribute="stripe_card_expiry",
        widget=ForeignKeyWidget(Profile, "stripe_card_expiry"),
    )

    stripe_payment_method_id = fields.Field(
        column_name="stripe_payment_method_id",
        attribute="stripe_payment_method_id",
        widget=ForeignKeyWidget(Profile, "stripe_payment_method_id"),
    )

    stripe_subscription_id = fields.Field(
        column_name="stripe_subscription_id",
        attribute="stripe_subscription_id",
        widget=ForeignKeyWidget(Profile, "stripe_subscription_id"),
    )

    subscription_status = fields.Field(
        column_name="subscription_status",
        attribute="subscription_status",
        widget=ForeignKeyWidget(Profile, "subscription_status"),
    )

    def dehydrate_first_name(self, user):
        try:
            return user.profile.first_name
        except Exception:
            return ""

    def dehydrate_last_name(self, user):
        try:
            return user.profile.last_name
        except Exception:
            return ""

    def dehydrate_screen_name_name(self, user):
        try:
            return user.profile.screen_name
        except Exception:
            return ""

    def dehydrate_rfid(self, user):
        try:
            return user.profile.rfid
        except Exception:
            return None

    def dehydrate_state(self, user):
        try:
            return user.profile.state
        except Exception:
            return "noob"

    def dehydrate_stripe_customer_id(self, user):
        try:
            return user.profile.stripe_customer_id
        except Exception:
            return ""

    def dehydrate_stripe_card_expiry(self, user):
        try:
            return user.profile.stripe_card_expiry
        except Exception:
            return ""

    def dehydrate_stripe_payment_method_id(self, user):
        try:
            return user.profile.stripe_payment_method_id
        except Exception:
            return ""

    def dehydrate_stripe_subscription_id(self, user):
        try:
            return user.profile.stripe_subscription_id
        except Exception:
            return ""

    def dehydrate_subscription_status(self, user):
        try:
            return user.profile.subscription_status
        except Exception:
            return "inactive"

    def before_import_row(self, row, **kwargs):

        user, created = User.objects.get_or_create(
            email=row["email"],
            defaults={
                "email": row["email"],
                "email_verified": True,
                "admin": row["admin"],
                "staff": row["staff"],
            },
        )

        print(f"{user=}, {created=}")
        # new User needs a Profile
        if created:
            # mandatory fields with profile
            created_profile = Profile.objects.create(
                user=user,
                first_name=row["first_name"],
                last_name=row["last_name"],
                screen_name=row["screen_name"],
                rfid=row["rfid"] or None,
                # non-mandatory
                # state is case Sensitive (Needs Induction, Active, Inactive, Account only)
                state=row["state"] or None,
                stripe_customer_id=row["stripe_customer_id"] or None,
                stripe_card_expiry=row["stripe_card_expiry"] or None,
                stripe_payment_method_id=row["stripe_payment_method_id"] or None,
                stripe_subscription_id=row["stripe_subscription_id"] or None,
                # subxcription status is case sensitive (Active, Inactive, Cancelling)
                subscription_status=row["subscription_status"] or "inactive",
            )
            # created_profile.log_event(
            # description="updated subscription info", event_type="profile"
            # )

            # created_profile.activate()

    def skip_row(self, instance, original, row, import_validation_errors):
        return row["email"] == "default@example.com"

    class Meta:
        model = User
        import_id_fields = ["email"]
        fields = (
            "email",
            "staff",
            "admin",
            "first_name",
            "last_name",
            "screen_name",
            "rfid",
            "state",
            "stripe_customer_id",
            "stripe_card_expiry",
            "stripe_payment_method_id",
            "stripe_subscription_id",
            "subscription_status",
        )


@admin.register(User)
class AdminLogAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    resource_class = UserResource
    pass


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    readonly_fields = ("created", "subscription_first_created")
    pass


@admin.register(UserEventLog)
class UserEventLogAdmin(admin.ModelAdmin):
    readonly_fields = ("date",)


@admin.register(EventLog)
class EventLogAdmin(admin.ModelAdmin):
    readonly_fields = ("date",)

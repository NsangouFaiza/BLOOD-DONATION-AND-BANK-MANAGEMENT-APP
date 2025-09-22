from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta

from .models import Appointment, BloodRequest, TransfusionReport, Notification, DonorPatientMatch


def notify(user, ntype, title, message, priority="medium"):
    try:
        Notification.objects.create(
            user=user,
            notification_type=ntype,
            title=title,
            message=message,
            priority=priority,
        )
    except Exception:
        # Avoid breaking the main transaction if notifications fail
        pass


@receiver(post_save, sender=Appointment)
def appointment_created_or_updated(sender, instance: Appointment, created, **kwargs):
    """Notify involved parties when an appointment is created/updated.
    Also, when completed, schedule a donor reminder for the next eligible donation date (56 days).
    """
    donor_user = instance.donor.user

    if created:
        # Notify donor
        notify(
            donor_user,
            "appointment",
            "Appointment Scheduled",
            f"Your donation appointment is scheduled for {instance.appointment_date} at {instance.appointment_time}.",
        )
    else:
        notify(
            donor_user,
            "appointment",
            "Appointment Updated",
            f"Your appointment on {instance.appointment_date} is now '{instance.get_status_display()}'.",
        )

    # If completed, send next-eligibility reminder
    if instance.status == "completed":
        next_date = instance.appointment_date + timedelta(days=56)
        notify(
            donor_user,
            "appointment",
            "Thank you for donating!",
            f"You're eligible to donate again on {next_date.strftime('%Y-%m-%d')}.",
            priority="high",
        )


@receiver(pre_save, sender=BloodRequest)
def capture_previous_status(sender, instance: BloodRequest, **kwargs):
    if instance.pk:
        try:
            prev = BloodRequest.objects.get(pk=instance.pk)
            instance._previous_status = prev.status
        except BloodRequest.DoesNotExist:
            instance._previous_status = None
    else:
        instance._previous_status = None


@receiver(post_save, sender=BloodRequest)
def blood_request_status_notify(sender, instance: BloodRequest, created, **kwargs):
    patient_user = instance.patient.user
    if created:
        notify(
            patient_user,
            "blood_request",
            "Blood Request Submitted",
            f"Your request for {instance.blood_type_needed} has been submitted.",
        )
    else:
        prev = getattr(instance, "_previous_status", None)
        if prev and prev != instance.status:
            notify(
                patient_user,
                "blood_request",
                "Request Status Updated",
                f"Your request is now '{instance.get_status_display()}'.",
            )


@receiver(post_save, sender=TransfusionReport)
def transfusion_report_logged(sender, instance: TransfusionReport, created, **kwargs):
    if not created:
        return
    # Notify patient
    notify(
        instance.patient.user,
        "system",
        "Transfusion Report Logged",
        "A transfusion report was recorded for your case.",
        priority="high",
    )
    # If a blood unit is linked, try to thank the donor via recent match
    if instance.blood_unit and instance.blood_unit.donor:
        donor_user = instance.blood_unit.donor.user
        notify(
            donor_user,
            "system",
            "Your Donation Helped a Patient",
            "Thank you! Your donated blood was successfully used to help a patient.",
            priority="high",
        )

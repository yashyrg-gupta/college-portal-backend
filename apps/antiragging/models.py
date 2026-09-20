from django.db import models
from apps.accounts.models import SoftDeleteModel
from simple_history.models import HistoricalRecords
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
import re


class ResourceCategory(models.TextChoices):
    UGC_REGULATIONS = "ugc_regulations", "UGC Regulations"
    UNIVERSITY_POLICY = "university_policy", "University Policy"
    AWARENESS_MATERIAL = "awareness_material", "Awareness Material"
    ANNUAL_REPORT = "annual_report", "Annual Compliance Report"
    HOSTEL_SAFETY = "hostel_safety", "Hostel Safety"


class Resource(SoftDeleteModel):
    title = models.CharField(max_length=255)
    category = models.CharField(max_length=32, choices=ResourceCategory.choices)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to="antiragging/resources/")
    published_on = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    history = HistoricalRecords()

    class Meta:
        ordering = ["-published_on"]

    def __str__(self):
        return self.title


class CommitteeType(models.TextChoices):
    ANTI_RAGGING_COMMITTEE = "committee", "Anti-Ragging Committee"
    ANTI_RAGGING_SQUAD = "squad", "Anti-Ragging Squad"


class CommitteeMember(SoftDeleteModel):
    designation_choices = [
        ("", "Select Designation"),
        ("CHAIRPERSON", "Chairperson"),
        ("MEMBER", "Member"),
        ("CONVENER","Convener"),
        ("MEMBER_CONVENER", "Member & Convener"),
        ("OTHER", "Other"),
    ]
    faculty = models.ForeignKey(
        "faculty.Faculty",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="antiragging_committee_members",
        verbose_name="Member Name (Faculty)",
        help_text="Select faculty member, or leave blank and enter name below for external/non-teaching members.",
    )
    name = models.CharField(
        max_length=150,
        blank=True,
        verbose_name="Member Name (Non-Teaching/External Member)",
        help_text="Required if not selecting a faculty member above.",
    )
    affiliation = models.CharField(
        max_length=150,
        blank=True,
        verbose_name="Designation in Committee"
    )
    designation = models.CharField(max_length=150, choices=designation_choices)
    other_designation = models.CharField(
        max_length=150,
        blank=True,
        verbose_name="Specify Other Designation",
        help_text="Required if Designation is 'Other'",
    )
    committee_type = models.CharField(max_length=16, choices=CommitteeType.choices)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    display_order = models.PositiveIntegerField()
    history = HistoricalRecords()

    class Meta:
        ordering = ["committee_type", "display_order"]

    @property
    def member_name(self):
        if self.faculty:
            return self.faculty.name
        return self.name

    def clean(self):
        super().clean()
        if not self.faculty and not (self.name and self.name.strip()):
            raise ValidationError(
                {"name": "Please either select a Faculty member or enter the Member Name for non-teaching/external members."}
            )
        if self.designation == "OTHER" and not (self.other_designation and self.other_designation.strip()):
            raise ValidationError(
                {"other_designation": "Please specify the designation when 'Other' is selected."}
            )
        if self.phone:
            val = str(self.phone).strip()
            if not re.match(r"^\d{10}$", val):
                raise ValidationError(
                    {"phone": "Phone number must be exactly 10 digits."}
                )
            self.phone = val

        if self.email:
            val = str(self.email).strip().lower()
            try:
                validate_email(val)
            except ValidationError:
                raise ValidationError(
                    {"email": "Please enter a valid email address."}
                )
            self.email = val

    def __str__(self):
        name_str = self.member_name or "Unknown Member"
        return f"{name_str} ({self.get_committee_type_display()})"


class FAQ(SoftDeleteModel):
    question = models.CharField(max_length=255)
    answer = models.TextField()
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    history = HistoricalRecords()

    class Meta:
        ordering = ["display_order", "id"]
        verbose_name = "Anti-Ragging FAQ"
        verbose_name_plural = "Anti-Ragging FAQs"

    def __str__(self):
        return self.question


class EmergencyContact(SoftDeleteModel):
    name = models.CharField(max_length=150)
    role = models.CharField(max_length=150)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    available_hours = models.CharField(max_length=100, blank=True, help_text="e.g. 24x7 or 9:00 AM - 5:00 PM")
    display_order = models.PositiveIntegerField(default=0)
    history = HistoricalRecords()

    class Meta:
        ordering = ["display_order", "name"]
        
    def clean(self):
        super().clean()
        if self.phone:
            val = str(self.phone).strip()
            if not re.match(r"^\d{10}$", val):
                raise ValidationError(
                    {"phone": "Phone number must be exactly 10 digits."}
                )
            self.phone = val

        if self.email:
            val = str(self.email).strip().lower()
            try:
                validate_email(val)
            except ValidationError:
                raise ValidationError(
                    {"email": "Please enter a valid email address."}
                )
            self.email = val

    def __str__(self):
        return f"{self.name} - {self.role}"

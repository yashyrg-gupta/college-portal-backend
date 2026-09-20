from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from apps.accounts.models import SoftDeleteModel
from simple_history.models import HistoricalRecords

User = get_user_model()


# ─────────────────────────────────────────────
#  Grievance Redressal Portal
# ─────────────────────────────────────────────


class Grievance(SoftDeleteModel):

    NATURE_OF_GRIEVANCE_CHOICES = [

        ("ragging", "Ragging Related"),
        ("admission","Admission Related"),
        ("examination","Examination Related"),
        ("unfair_means","Unfair Means Related"),
        ("scholarship","Scholarship Related"),
        ("Other", "Others"),
    ]

    COMPLAINANT_TYPE_CHOICES = [
        ("student", "Student"),
        ("faculty", "Faculty"),
        ("non_teaching_staff", "Non Teaching Staff"),
        ("Other", "Others"),
    ]

    GENDER_CHOICES = [
        ("male", "Male"),
        ("female", "Female"),
        ("other", "Other"),
    ]

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("under_review", "Under Review"),
        ("forwarded", "Forwarded to Higher Authority"),
        ("resolved", "Resolved"),
        ("rejected", "Rejected"),
    ]

    tracking_id = models.CharField(max_length=50, unique=True, blank=True, null=True)

    nature_of_grievance = models.CharField(
        max_length=100,
        choices=NATURE_OF_GRIEVANCE_CHOICES,
        verbose_name="Nature of Grievance",
    )
    others_nature_of_grievance = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Specify Other Nature of Grievance",
        help_text="Required if Nature of Grievance is 'Others'",
    )

    complainant_type = models.CharField(
        max_length=50,
        choices=COMPLAINANT_TYPE_CHOICES,
        verbose_name="Complainant",
    )
    others_complainant_type = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Specify Other Complainant Type",
        help_text="Required if Complainant Type is 'Others'",
    )

    name_of_complainant = models.CharField(
        max_length=255,
        verbose_name="Name of Complainant",
    )

    aadhaar_number = models.CharField(
        max_length=12,
        verbose_name="Aadhaar Number",
    )
    enrollment_id = models.CharField(
        max_length=100,
        verbose_name="Enrollment / Official ID No.",
    )
    date_of_birth = models.DateField(
        verbose_name="Date of Birth",
    )
    gender = models.CharField(
        max_length=20,
        choices=GENDER_CHOICES,
        verbose_name="Gender",
    )
    fathers_name = models.CharField(
        max_length=255,
        verbose_name="Father's Name",
    )
    mothers_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Mother's Name",
    )
    permanent_address = models.TextField(
        verbose_name="Permanent Address",
    )
    state = models.CharField(
        max_length=100,
        verbose_name="State",
    )
    city = models.CharField(
        max_length=100,
        verbose_name="City",
    )
    pincode = models.CharField(
        max_length=10,
        verbose_name="Pincode",
    )

    contact_number = models.CharField(
        max_length=15,
        verbose_name="Contact No.",
    )
    email = models.EmailField(
        verbose_name="Email",
    )
    complaint_text = models.TextField(
        verbose_name="Complaint",
        help_text="Maximum 500 characters.",
    )

    declaration_accepted = models.BooleanField(
        default=False,
        verbose_name="Declaration Accepted",
    )

    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default="pending",
    )
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    history = HistoricalRecords()

    class Meta:
        verbose_name = "Grievance"
        verbose_name_plural = "Grievances"
        ordering = ["-submitted_at"]
        permissions = [
            (
                "manage_grievances",
                "Can view and update grievance case statuses through the API",
            ),
        ]

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new and not self.tracking_id:
            month_str = self.submitted_at.strftime("%Y%m")
            self.tracking_id = f"GRV-{month_str}-{self.id:04d}"
            self.save(update_fields=["tracking_id"])

    def clean(self):
        super().clean()
        if self.nature_of_grievance == "Other" and not self.others_nature_of_grievance:
            raise ValidationError(
                {"others_nature_of_grievance": "This field is required."}
            )
        if self.complainant_type == "Other" and not self.others_complainant_type:
            raise ValidationError(
                {"others_complainant_type": "This field is required."}
            )

    def __str__(self):
        return f"{self.tracking_id} — {self.name_of_complainant} ({self.get_status_display()})"


class GrievanceAttachment(SoftDeleteModel):

    grievance = models.ForeignKey(
        Grievance,
        related_name="attachments",
        on_delete=models.CASCADE,
    )
    file = models.FileField(upload_to="grievance_attachments/%Y/%m/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Attachment"
        verbose_name_plural = "Attachments"

    def __str__(self):
        return f"Attachment for {self.grievance.tracking_id}"


class GrievanceSignature(SoftDeleteModel):

    grievance = models.OneToOneField(
        Grievance,
        related_name="signature",
        on_delete=models.CASCADE,
    )
    image = models.ImageField(upload_to="grievance_signatures/%Y/%m/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Signature"
        verbose_name_plural = "Signatures"

    def __str__(self):
        return f"Signature for {self.grievance.tracking_id}"


class GrievanceActionLog(SoftDeleteModel):
    grievance = models.ForeignKey(
        Grievance,
        related_name="action_logs",
        on_delete=models.CASCADE,
    )
    action_taken_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True
    )
    action_description = models.TextField()
    status_changed_to = models.CharField(
        max_length=30,
        choices=Grievance.STATUS_CHOICES,
        blank=True,
        null=True,
    )
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Grievance Action Log"
        verbose_name_plural = "Grievance Action Logs"
        ordering = ["timestamp"]

    def __str__(self):
        return f"Log for {self.grievance.tracking_id} at {self.timestamp}"


# Internal Complaints Committee (ICC) Portal


class ICCComplaint(SoftDeleteModel):
    ICC_NATURE_CHOICES = [
        ("sexual_harassment", "Sexual Harassment"),
        ("workplace_bullying", "Workplace Bullying"),
        ("discrimination", "Discrimination"),
        ("Other", "Other"),
    ]

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("under_review", "Under Review"),
        ("forwarded", "Forwarded to Higher Authority"),
        ("closed", "Closed"),
        ("rejected", "Rejected"),
    ]

    tracking_id = models.CharField(max_length=50, unique=True, blank=True, null=True)

    nature_of_grievance = models.CharField(
        max_length=100,
        choices=ICC_NATURE_CHOICES,
        verbose_name="Nature of Grievance",
    )
    others_nature_of_grievance = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Specify Other Nature of Grievance",
        help_text="Required if Nature of Grievance is 'Other'",
    )

    name_of_complainant = models.CharField(
        max_length=255,
        verbose_name="Name of Complainant",
    )

    aadhaar_number = models.CharField(
        max_length=12,
        verbose_name="Aadhaar Number",
    )

    enrollment_id = models.CharField(
        max_length=50,
        verbose_name="Enrollment / Official ID No.",
    )

    date_of_birth = models.DateField(
        verbose_name="Date of Birth",
    )

    GENDER_CHOICES = [
        ("male", "Male"),
        ("female", "Female"),
        ("other", "Other"),
    ]
    gender = models.CharField(
        max_length=20,
        choices=GENDER_CHOICES,
        verbose_name="Gender",
    )

    fathers_name = models.CharField(
        max_length=255,
        verbose_name="Father's Name",
    )

    mothers_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Mother's Name",
    )

    permanent_address = models.TextField(
        verbose_name="Permanent Address",
    )

    state = models.CharField(
        max_length=100,
        verbose_name="State",
    )

    city = models.CharField(
        max_length=100,
        verbose_name="City",
    )

    pincode = models.CharField(
        max_length=20,
        verbose_name="Pincode",
    )

    contact_number = models.CharField(
        max_length=15,
        verbose_name="Contact No.",
    )

    email = models.EmailField(
        verbose_name="Email",
    )

    complaint_text = models.TextField(
        verbose_name="Complaint",
        help_text="Maximum 2000 characters.",
    )

    declaration_accepted = models.BooleanField(
        default=False,
        verbose_name="Declaration Accepted",
    )

    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default="pending",
    )
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    history = HistoricalRecords()

    class Meta:
        verbose_name = "ICC Complaint"
        verbose_name_plural = "ICC Complaints"
        ordering = ["-submitted_at"]

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new and not self.tracking_id:
            month_str = self.submitted_at.strftime("%Y%m")
            self.tracking_id = f"ICC-{month_str}-{self.id:04d}"
            self.save(update_fields=["tracking_id"])

    def __str__(self):
        return f"{self.tracking_id} — {self.name_of_complainant} ({self.get_status_display()})"


class ICCAttachment(SoftDeleteModel):
    complaint = models.ForeignKey(
        ICCComplaint,
        related_name="attachments",
        on_delete=models.CASCADE,
    )
    file = models.FileField(upload_to="icc_attachments/%Y/%m/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "ICC Attachment"
        verbose_name_plural = "ICC Attachments"


class ICCSignature(SoftDeleteModel):
    complaint = models.OneToOneField(
        ICCComplaint,
        related_name="signature",
        on_delete=models.CASCADE,
    )
    image = models.ImageField(upload_to="icc_signatures/%Y/%m/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Signature"
        verbose_name_plural = "Signatures"


class ICCActionLog(SoftDeleteModel):
    complaint = models.ForeignKey(
        ICCComplaint,
        related_name="action_logs",
        on_delete=models.CASCADE,
    )
    action_taken_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True
    )
    action_description = models.TextField()
    status_changed_to = models.CharField(
        max_length=30,
        choices=ICCComplaint.STATUS_CHOICES,
        blank=True,
        null=True,
    )
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "ICC Action Log"
        verbose_name_plural = "ICC Action Logs"
        ordering = ["timestamp"]


# SC/ST, OBC, Disable & Minority Discrimination Complaint Portal


class DiscriminationComplaint(SoftDeleteModel):
    DISCRIMINATION_CHOICES = [
        ("sc_st", "SC/ST"),
        ("obc", "OBC"),
        ("disable", "Disable (PwD)"),
        ("minority", "Minority"),
        ("Other", "Other"),
    ]
    MARITAL_STATUS_CHOICES = [
        ("single", "Single"),
        ("married", "Married"),
        ("widowed", "Widowed"),
        ("divorced", "Divorced"),
        ("separated", "Separated"),
    ]
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("under_review", "Under Review"),
        ("forwarded", "Forwarded to Higher Authority"),
        ("closed", "Closed"),
        ("rejected", "Rejected"),
    ]
    tracking_id = models.CharField(max_length=50, unique=True, blank=True, null=True)
    # Complaint Details
    complaint_discrimination = models.CharField(
        max_length=50,
        choices=DISCRIMINATION_CHOICES,
        verbose_name="Complaint Discrimination",
    )
    others_complaint_discrimination = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Specify Other Complaint Discrimination",
        help_text="Required if Complaint Discrimination is 'Other'",
    )
    complaint_text = models.TextField(
        verbose_name="Complaint Details",
        help_text="Maximum 2000 characters.",
    )
    # University Details (Optional except where noted)
    enrollment_id = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Enrollment / Official ID No.",
    )
    roll_no = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Roll No",
    )
    school_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="School's Name",
    )
    department_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Department's Name",
    )
    course_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Course's Name",
    )
    # Basic Details
    full_name = models.CharField(
        max_length=255,
        verbose_name="Full Name",
    )
    aadhaar_number = models.CharField(
        max_length=12,
        verbose_name="Aadhaar Number",
    )
    date_of_birth = models.DateField(
        verbose_name="Date of Birth",
    )
    marital_status = models.CharField(
        max_length=50,
        choices=MARITAL_STATUS_CHOICES,
        verbose_name="Marital Status",
    )
    GENDER_CHOICES = [
        ("male", "Male"),
        ("female", "Female"),
        ("other", "Other"),
    ]
    gender = models.CharField(
        max_length=20,
        choices=GENDER_CHOICES,
        verbose_name="Gender",
    )
    category_belonging = models.CharField(
        max_length=50,
        choices=DISCRIMINATION_CHOICES,
        verbose_name="Category you belong",
    )
    fathers_name = models.CharField(
        max_length=255,
        verbose_name="Father's Name",
    )
    mothers_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Mother's Name",
    )
    # Contact Details
    contact_number = models.CharField(
        max_length=15,
        verbose_name="Contact No",
    )
    email = models.EmailField(
        blank=True,
        null=True,
        verbose_name="Email ID",
    )
    permanent_address = models.TextField(
        verbose_name="Permanent Address",
    )
    state = models.CharField(
        max_length=100,
        verbose_name="State",
    )
    city = models.CharField(
        max_length=100,
        verbose_name="City",
    )
    pincode = models.CharField(
        max_length=20,
        verbose_name="Pin-code",
    )
    declaration_accepted = models.BooleanField(
        default=False,
        verbose_name="Declaration Accepted",
    )
    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default="pending",
    )
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    history = HistoricalRecords()

    class Meta:
        verbose_name = "Discrimination Complaint"
        verbose_name_plural = "Discrimination Complaints"
        ordering = ["-submitted_at"]

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new and not self.tracking_id:
            month_str = self.submitted_at.strftime("%Y%m")
            self.tracking_id = f"DSC-{month_str}-{self.id:04d}"
            self.save(update_fields=["tracking_id"])

    def __str__(self):
        return f"{self.tracking_id} — {self.full_name} ({self.get_status_display()})"


class DiscriminationAttachment(SoftDeleteModel):
    complaint = models.ForeignKey(
        DiscriminationComplaint,
        related_name="attachments",
        on_delete=models.CASCADE,
    )
    file = models.FileField(upload_to="discrimination_attachments/%Y/%m/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Attachment"
        verbose_name_plural = "Attachments"


class DiscriminationSignature(SoftDeleteModel):
    complaint = models.OneToOneField(
        DiscriminationComplaint,
        related_name="signature",
        on_delete=models.CASCADE,
    )
    image = models.ImageField(upload_to="discrimination_signatures/%Y/%m/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Discrimination Signature"
        verbose_name_plural = "Discrimination Signatures"


class DiscriminationActionLog(SoftDeleteModel):
    complaint = models.ForeignKey(
        DiscriminationComplaint,
        related_name="action_logs",
        on_delete=models.CASCADE,
    )
    action_taken_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True
    )
    action_description = models.TextField()
    status_changed_to = models.CharField(
        max_length=30,
        choices=DiscriminationComplaint.STATUS_CHOICES,
        blank=True,
        null=True,
    )
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Discrimination Action Log"
        verbose_name_plural = "Discrimination Action Logs"
        ordering = ["timestamp"]


# ─────────────────────────────────────────────────────────────────────────────
# Student Feedback Portal
# ─────────────────────────────────────────────────────────────────────────────


class StudentFeedback(SoftDeleteModel):
    SUBJECT_CHOICES = [
        ("academic", "Academic"),
        ("infrastructure", "Infrastructure"),
        ("hostel", "Hostel"),
        ("extracurricular", "Extracurricular Activities"),
        ("administration", "Administration"),
        ("Other", "Other"),
    ]

    COURSE_CHOICES = [
        ("ug", "Undergraduate"),
        ("pg", "Postgraduate"),
        ("phd", "Ph.D."),
        ("diploma", "Diploma"),
        ("Other", "Other"),
    ]

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("under_review", "Under Review"),
        ("action_taken", "Action Taken"),
        ("closed", "Closed"),
    ]

    tracking_id = models.CharField(max_length=50, unique=True, blank=True, null=True)

    subject_of_feedback = models.CharField(
        max_length=100,
        choices=SUBJECT_CHOICES,
        verbose_name="Subject of your Feedback",
    )
    others_subject_of_feedback = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Specify Other Subject of Feedback",
        help_text="Required if Subject of Feedback is 'Other'",
    )
    name_of_student = models.CharField(
        max_length=255,
        verbose_name="Name of Student",
    )
    aadhaar_number = models.CharField(
        max_length=12,
        verbose_name="Aadhaar Number",
    )
    fathers_name = models.CharField(
        max_length=255,
        verbose_name="Father's Name",
    )
    mothers_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Mother's Name",
    )
    permanent_address = models.TextField(
        verbose_name="Permanent Address",
    )
    state = models.CharField(
        max_length=100,
        verbose_name="State",
    )
    city = models.CharField(
        max_length=100,
        verbose_name="City",
    )
    pincode = models.CharField(
        max_length=20,
        verbose_name="Pincode",
    )
    contact_number = models.CharField(
        max_length=15,
        verbose_name="Contact No",
    )
    email = models.EmailField(
        verbose_name="Email",
    )
    course_name = models.CharField(
        max_length=100,
        choices=COURSE_CHOICES,
        verbose_name="Course Name",
    )
    date_of_birth = models.DateField(
        verbose_name="Date of Birth",
    )
    GENDER_CHOICES = [
        ("male", "Male"),
        ("female", "Female"),
        ("other", "Other"),
    ]
    gender = models.CharField(
        max_length=20,
        choices=GENDER_CHOICES,
        verbose_name="Gender",
    )
    roll_no = models.CharField(
        max_length=50,
        verbose_name="Roll No.",
    )
    enrollment_no = models.CharField(
        max_length=50,
        verbose_name="Enrollment No.",
    )
    feedback_text = models.TextField(
        verbose_name="Feedback",
        help_text="Maximum 2000 characters.",
    )

    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default="pending",
    )
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    history = HistoricalRecords()

    class Meta:
        verbose_name = "Student Feedback"
        verbose_name_plural = "Student Feedbacks"
        ordering = ["-submitted_at"]

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new and not self.tracking_id:
            month_str = self.submitted_at.strftime("%Y%m")
            self.tracking_id = f"FDBK-{month_str}-{self.id:04d}"
            self.save(update_fields=["tracking_id"])

    def __str__(self):
        return (
            f"{self.tracking_id} — {self.name_of_student} ({self.get_status_display()})"
        )


class FeedbackAttachment(SoftDeleteModel):
    feedback = models.ForeignKey(
        StudentFeedback,
        related_name="attachments",
        on_delete=models.CASCADE,
    )
    file = models.FileField(upload_to="feedback_attachments/%Y/%m/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Attachment"
        verbose_name_plural = "Attachments"


class FeedbackSignature(SoftDeleteModel):
    feedback = models.OneToOneField(
        StudentFeedback,
        related_name="signature",
        on_delete=models.CASCADE,
    )
    image = models.ImageField(upload_to="feedback_signatures/%Y/%m/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Feedback Signature"
        verbose_name_plural = "Feedback Signatures"


class FeedbackActionLog(SoftDeleteModel):
    feedback = models.ForeignKey(
        StudentFeedback,
        related_name="action_logs",
        on_delete=models.CASCADE,
    )
    action_taken_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True
    )
    action_description = models.TextField()
    status_changed_to = models.CharField(
        max_length=30,
        choices=StudentFeedback.STATUS_CHOICES,
        blank=True,
        null=True,
    )
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Feedback Action Log"
        verbose_name_plural = "Feedback Action Logs"
        ordering = ["timestamp"]

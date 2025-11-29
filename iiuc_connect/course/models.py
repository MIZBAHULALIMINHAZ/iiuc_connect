import mongoengine as me
from accounts.models import Department, User 


class Course(me.Document):
    course_code = me.StringField(required=True, unique=True, max_length=20)  # Indexed unique
    department = me.ReferenceField(Department, reverse_delete_rule=me.CASCADE, required=True)  # FK relation
    credit_hour = me.IntField(required=True, min_value=0, max_value=5)

    # Cloudinary resource links (List of URLs)
    mid_theory_resources = me.ListField(me.URLField(), default=list)        # List of URLs
    mid_previous_solves = me.ListField(me.URLField(), default=list)
    final_resources = me.ListField(me.URLField(), default=list)
    final_previous_solves = me.ListField(me.URLField(), default=list)

    meta = {
        "collection": "courses",
        "indexes": [
            "course_code",
            "department",
        ],
        "ordering": ["course_code"],  # Default sort by course_code
    }

    def __str__(self):
        return f"{self.course_code} ({self.department.name})"

class CourseRegistration(me.Document):
    student = me.ReferenceField(User, reverse_delete_rule=me.CASCADE, required=True)
    course = me.ReferenceField(Course, reverse_delete_rule=me.CASCADE, required=True)
    status = me.StringField(choices=["pending", "confirmed"], default="pending")
    section = me.StringField(required=True)

    meta = {
        "collection": "course_registrations",
        "indexes": ["student", "course", "status"],
        "unique_together": [("student", "course")]
    }

    def __str__(self):
        return f"{self.student.email} → {self.course.course_code} ({self.status})"


class Payment(me.Document):
    registration = me.ReferenceField(CourseRegistration, reverse_delete_rule=me.CASCADE, required=True,unique=True)
    amount = me.FloatField(required=True)
    method = me.StringField(choices=["bkash", "nagad", "rocket"], required=True)
    status = me.StringField(choices=["pending", "completed", "failed"], default="pending")
    transaction_id = me.StringField()

    meta = {
        "collection": "payments",
        "indexes": [
            {"fields": ["registration"], "unique": True},
            "status",
        ],
    }

    def __str__(self):
        return f"{self.registration.student.email} → {self.amount} ({self.status})"
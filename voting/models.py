from django.db import models
from cloudinary.models import CloudinaryField
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager

from django.db import models

class Position(models.Model):
    IMPORTANCE_CHOICES = [
        (1, "1 - Very High"),
        (2, "2 - High"),
        (3, "3"),
        (4, "4"),
        (5, "5 - Medium"),
        (6, "6"),
        (7, "7"),
        (8, "8"),
        (9, "9"),
        (10, "10 - Low"),
        (11, "11 - Very Low"),
        (12, "12 - Lowest"),
    ]

    name = models.CharField(max_length=100)
    importance = models.PositiveIntegerField(choices=IMPORTANCE_CHOICES)

    def __str__(self):
        return self.name


class StudentManager(BaseUserManager):
    def create_user(self, reg_number, full_name, password=None):
        if not reg_number:
            raise ValueError('The Registration Number must be set')
        student = self.model(reg_number=reg_number, full_name=full_name)
        student.set_password(password)  # Use set_password to handle hashing
        student.save(using=self._db)
        return student

    def create_superuser(self, reg_number, full_name, password=None):
        if not reg_number:
            raise ValueError('The Registration Number must be set')
        student = self.create_user(
            reg_number=reg_number,
            full_name=full_name,
            password=password
        )
        student.is_staff = True
        student.is_superuser = True
        student.save(using=self._db)
        return student

class Student(AbstractBaseUser):
    reg_number = models.CharField(max_length=100, unique=True)
    full_name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    USERNAME_FIELD = 'reg_number'
    REQUIRED_FIELDS = ['full_name']

    objects = StudentManager()

    def __str__(self):
        return self.full_name

    def has_voted_for_position(self, position):
        return Vote.objects.filter(student=self, position=position).exists()

    def get_remaining_positions(self):
        voted_positions = Vote.objects.filter(student=self).values_list('position_id', flat=True)
        return Position.objects.exclude(id__in=voted_positions).order_by('importance')

    # Required permission methods for Django admin
    def has_perm(self, perm, obj=None):
        """
        Return True if the user has the named permission. 
        For superusers, this always returns True.
        """
        if self.is_active and self.is_superuser:
            return True
        return False

    def has_perms(self, perm_list, obj=None):
        """
        Return True if the user has each of the named permissions.
        """
        return all(self.has_perm(perm, obj) for perm in perm_list)

    def has_module_perms(self, app_label):
        """
        Return True if the user has any permissions in the given app label.
        For superusers, this always returns True.
        """
        if self.is_active and self.is_superuser:
            return True
        return False

class Contestant(models.Model):
    position = models.ForeignKey(Position, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    image = CloudinaryField('contestants')

    def __str__(self):
        return f"{self.name} - {self.position.name}"


class Vote(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    position = models.ForeignKey(Position, on_delete=models.CASCADE)
    contestant = models.ForeignKey(Contestant, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['student', 'position'], name='unique_vote_per_position')
        ]

    def __str__(self):
        return f"{self.student.full_name} voted for {self.contestant.name} in {self.position.name}"

    @classmethod
    def validate_vote(cls, student, position):
        return cls.objects.filter(student=student, position=position).exists()


class ElectionSettings(models.Model):
    """Single-row switch controlling whether students can currently log in and vote."""
    is_open = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Election Setting"
        verbose_name_plural = "Election Settings"

    def __str__(self):
        return "Election OPEN" if self.is_open else "Election CLOSED"

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
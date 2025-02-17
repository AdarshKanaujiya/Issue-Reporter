from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now
import uuid

class Issue(models.Model):
    CATEGORY_CHOICES = [
        ('Road', 'Road'),
        ('Electricity', 'Electricity'),
        ('Water', 'Water'),
        ('Internet', 'Internet'),
        ('Public Transport', 'Public Transport'),
        ('Waste Management', 'Waste Management'),
        ('Other', 'Other'),
    ]
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('In Progress', 'In Progress'),
        ('Resolved', 'Resolved'),
        ('Sent to Government', 'Sent to Government'),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='Other')
    location = models.CharField(max_length=255, blank=True, default="")  # Allow empty location
    image = models.ImageField(upload_to='issue_images/', null=True, blank=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='Pending')
    votes_count = models.IntegerField(default=0)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)  # Allow anonymous reporting
    lat = models.FloatField(null=True, blank=True)  # Latitude
    lng = models.FloatField(null=True, blank=True)  # Longitude
    created_at = models.DateTimeField(auto_now_add=True)
    token = models.CharField(max_length=255, default=uuid.uuid4, unique=True)  # Add a token field

    def __str__(self):
        return self.title


class Comment(models.Model):
    issue = models.ForeignKey(Issue, on_delete=models.CASCADE, related_name='comments')
    user = models.CharField(max_length=100, default='Guest')  # Store user name as a string
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Comment by {self.user} on {self.issue.title}'


class Vote(models.Model):
    VOTE_CHOICES = [
        ('Upvote', 'Upvote'),
        ('Downvote', 'Downvote'),
    ]
    issue = models.ForeignKey(Issue, on_delete=models.CASCADE, related_name='votes')
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)  # Optional user
    ip_address = models.GenericIPAddressField(null=True, blank=True)  # Store voter’s IP
    vote_type = models.CharField(max_length=10, choices=VOTE_CHOICES)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['issue', 'user'], name='unique_vote_per_user',
                condition=models.Q(user__isnull=False)  # Unique per user
            ),
            models.UniqueConstraint(
                fields=['issue', 'ip_address'], name='unique_vote_per_ip',
                condition=models.Q(ip_address__isnull=False)  # Unique per IP
            )
        ]

    def __str__(self):
        if self.user:
            return f'{self.vote_type} by {self.user.username} on {self.issue.title}'
        return f'{self.vote_type} from IP {self.ip_address} on {self.issue.title}'
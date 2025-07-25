from huggingface_hub import login
import os
import json
import uuid
from dotenv import load_dotenv
from PIL import Image
import torch
import requests
# from transformers import (
#     CLIPProcessor, 
#     CLIPModel,
#     AutoModelForImageClassification,
#     AutoImageProcessor
# )

load_dotenv()
token = os.getenv('API_TOKEN')
login(token)

from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponseBadRequest
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.db import models
from django.db.models import Count
from django.core.files.storage import default_storage
from django.core.mail import send_mail
from django.utils import timezone
from django.utils.timezone import now, timedelta
from .models import Issue, Comment, Vote
from .forms import IssueForm, CommentForm
# nsfw_processor = AutoImageProcessor.from_pretrained("google/vit-base-patch16-224")
# nsfw_model = AutoModelForImageClassification.from_pretrained("google/vit-base-patch16-224")
# model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
# processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")


VULGAR_WORDS = ['badword1', 'badword2', 'badword3']


def issues_view(request):
    # Fetch the issues from the database
    issues = Issue.objects.all()  # Replace with your actual model
    
    # Convert issues to a JSON-compatible format
    issues_data = [
        {
            'id': issue.id,
            'title': issue.title,
            'description': issue.description,
            'lat': issue.lat,
            'lng': issue.lng,
        }
        for issue in issues if issue.lat and issue.lng
    ]
    
    issues_json = json.dumps(issues_data)  # Convert to JSON format

    return render(request, 'your_template.html', {'issues_json': issues_json})


def add_comment(request, issue_id):
    issue = get_object_or_404(Issue, id=issue_id)
    
    if request.method == 'POST':
        comment_text = request.POST.get('text')
        
        # For anonymous commenting, we'll create a guest user-like model
        # Here we can store comments with a "guest" name or similar
        username = request.POST.get('username', 'Guest')  # Default to 'Guest' if no name provided
        
        # Create and save the new comment
        comment = Comment(user=username, text=comment_text, issue=issue)
        comment.save()
        
        # Redirect to the issue detail page after adding the comment
        return redirect('issue_detail', issue_id=issue.id)
    
    return render(request, 'reports/issue_detail.html', {'issue': issue})

def forward_to_government(request, issue_id):
    issue = get_object_or_404(Issue, id=issue_id)
    issue.status = 'Sent to Government'
    issue.save()

    # Send email to government official
    send_mail(
        f"Issue Forwarded: {issue.title}",
        f"Issue Description: {issue.description}\nLocation: {issue.location}",
        'from@example.com',
        ['government@example.com'],
        fail_silently=False,
    )

    return redirect('admin_dashboard')


def issue_list(request):
    issues = Issue.objects.all()  # Get all issues
    issues_json = json.dumps([{
        'id': issue.id,
        'title': issue.title,
        'status': issue.status,
        'description': issue.description,
        'location': issue.location,
        'lat': issue.lat,
        'lng': issue.lng,
    } for issue in issues])

    # Generate analytics data
    now = timezone.now()
    
    # Weekly analytics
    week_issues = Issue.objects.filter(created_at__gte=now-timezone.timedelta(days=7))
    week_data = [
        {'status': 'Pending', 'count': week_issues.filter(status='Pending').count()},
        {'status': 'In Progress', 'count': week_issues.filter(status='In Progress').count()},
        {'status': 'Resolved', 'count': week_issues.filter(status='Resolved').count()}
    ]
    
    # Monthly analytics
    month_issues = Issue.objects.filter(created_at__gte=now-timezone.timedelta(days=30))
    month_data = [
        {'status': 'Pending', 'count': month_issues.filter(status='Pending').count()},
        {'status': 'In Progress', 'count': month_issues.filter(status='In Progress').count()},
        {'status': 'Resolved', 'count': month_issues.filter(status='Resolved').count()}
    ]
    
    # Yearly analytics
    year_issues = Issue.objects.filter(created_at__gte=now-timezone.timedelta(days=365))
    year_data = [
        {'status': 'Pending', 'count': year_issues.filter(status='Pending').count()},
        {'status': 'In Progress', 'count': year_issues.filter(status='In Progress').count()},
        {'status': 'Resolved', 'count': year_issues.filter(status='Resolved').count()}
    ]
    
    analytics_json = json.dumps({
        'week': week_data,
        'month': month_data,
        'year': year_data
    })

    return render(request, 'reports/issue_list.html', {
        'issues': issues,
        'issues_json': issues_json,
        'analytics_json': analytics_json
    })



def issue_detail(request, issue_id):
    issue = get_object_or_404(Issue, id=issue_id)
    comment_form = CommentForm()
    return render(request, "reports/issue_detail.html", {"issue": issue, "comment_form": comment_form})





def report_issue(request):
    if request.method == "POST":
        title = request.POST.get("title")
        description = request.POST.get("description")
        category = request.POST.get("category")
        location = request.POST.get("location")
        lat = request.POST.get("lat")
        lng = request.POST.get("lng")
        image = request.FILES.get("image")
        user = request.user if request.user.is_authenticated else None  # Set user if logged in

        if not image:
            return JsonResponse({"error": "Please upload an image."}, status=400)

        # Save image temporarily
        temp_image_path = default_storage.save(f"temp/{image.name}", image)
        full_temp_image_path = os.path.join(default_storage.location, temp_image_path)

        # 1️⃣ Check if the image is relevant
        if not is_image_relevant(full_temp_image_path, title, description, category):
            default_storage.delete(temp_image_path)  # Delete irrelevant image
            return JsonResponse({"error": "Irrelevant image or description. Please upload a relevant image."}, status=400)

        # 2️⃣ Check for NSFW content
        if is_nsfw(full_temp_image_path):
            default_storage.delete(temp_image_path)  # Delete NSFW image
            return JsonResponse({"error": "Inappropriate image detected. Please upload a proper image."}, status=400)

        if not lat or not lng:
            default_storage.delete(temp_image_path)  # Delete image if location is missing
            return JsonResponse({"error": "Latitude or Longitude is missing"}, status=400)

        # Move the image to the permanent directory only if it passes all checks
        new_image_path = default_storage.save(f"issue_images/{image.name}", image)
        default_storage.delete(temp_image_path)  # Delete the temporary file

        # Create a unique token for the issue
        token = uuid.uuid4().hex

        # Save to database
        issue = Issue.objects.create(
            title=title,
            description=description,
            category=category,
            location=location if location else f"{lat}, {lng}",
            lat=lat,
            lng=lng,
            image=new_image_path,
            token=token,
            user=user,
        )

        return JsonResponse({"message": "Issue reported successfully!", "issue_id": issue.id, "token": token})

    return render(request, "reports/report_issue.html")



class CommentView(models.Model):
    issue = models.ForeignKey('Issue', on_delete=models.CASCADE, related_name='comment_view')
    user = models.CharField(max_length=100)  
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)  # Keep only this

    def _str_(self):
        return f'Comment by {self.user} on {self.issue.title}'


def delete_issue(request, issue_id):
    issue = get_object_or_404(Issue, id=issue_id)
    issue.delete()
    return redirect('issue_list')  # Redirect to issue list after deletion




def vote_issue(request, issue_id):
    if request.method == 'POST':
        vote_type = request.POST.get('vote_type')  # Get the vote type (Upvote or Downvote)

        # Check if vote_type is missing
        if not vote_type:
            return JsonResponse({"error": "Vote type is missing."}, status=400)

        issue = get_object_or_404(Issue, id=issue_id)

        # Identify user (use session or IP if not logged in)
        if request.user.is_authenticated:
            user_identifier = request.user
            ip_address = None
        else:
            user_identifier = None
            ip_address = request.META.get('REMOTE_ADDR')

        # Check if the user (or IP) has already voted
        if Vote.objects.filter(issue=issue, user=user_identifier).exists() or \
           Vote.objects.filter(issue=issue, ip_address=ip_address).exists():
            return JsonResponse({"error": "You have already voted on this issue."}, status=400)

        # Create the vote
        Vote.objects.create(
            issue=issue,
            user=user_identifier,
            ip_address=ip_address,
            vote_type=vote_type
        )

        # Update aggregated vote count
        upvotes = issue.votes.filter(vote_type="Upvote").count()
        downvotes = issue.votes.filter(vote_type="Downvote").count()
        issue.votes_count = upvotes - downvotes
        issue.save()

        return JsonResponse({"message": "Vote recorded successfully!"}, status=200)

    return JsonResponse({"error": "Invalid request method."}, status=405)


# Define the admin_dashboard view (you can customize it)
def admin_dashboard(request):
    return render(request, 'admin_dashboard.html')

def admin_login(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('admin_dashboard')  # Redirect to admin dashboard
    else:
        form = AuthenticationForm()
    return render(request, 'admin_login.html', {'form': form})

# Define the update_issue_status view (you can customize it)
def update_issue_status(request, issue_id):
    # Add logic to update issue status
    return render(request, 'update_issue_status.html', {'issue_id': issue_id})


def get_issue_data():
    issues = Issue.objects.all()  # Get all issues from the database
    cleaned_issues = []
    
    for issue in issues:
        lat, lng = None, None
        # If the location is stored as a string like "lat,lng"
        if issue.location:
            try:
                lat, lng = map(float, issue.location.split(','))
            except ValueError:
                pass  # Skip invalid location data
        
        # If lat and lng are still None, use default or skip
        if lat is None or lng is None:
            continue  # Skip this issue or set default values
            
        cleaned_issues.append({
            'id': issue.id,
            'title': issue.title,
            'description': issue.description,
            'lat': lat,
            'lng': lng,
        })
    
    return cleaned_issues


def search_issue(request):
    issues = None
    if 'token' in request.GET:
        token = request.GET['token']
        issues = Issue.objects.filter(token=token)
    
    return render(request, 'reports/search_issue.html', {'issues': issues})




def is_image_relevant(image, title, description, category):
    """Checks if the uploaded image is relevant to the issue using CLIP."""
    try:
        from transformers import CLIPProcessor, CLIPModel
        from PIL import Image
        model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
        processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
        image = Image.open(image).convert("RGB")
        
        # More specific text inputs for comparison
        text_inputs = [
            f"A photo showing {title} issue", 
            f"Image of {description}",
            f"{category} problem visible in photo",
            "A clear photo documenting a community issue",
            "A completely unrelated photo or meme",
            "A random image that doesn't match the issue",
            "A joke, meme, or personal photo",
            "Blurry, distorted, or irrelevant image"
        ]


        inputs = processor(text=text_inputs, images=image, return_tensors="pt", padding=True)

        # Process the image with the model
        outputs = model(**inputs)

        if isinstance(outputs, str):
            try:
                outputs = json.loads(outputs)  # Ensure JSON format
            except json.JSONDecodeError:
                print("[ERROR] Invalid JSON response from model. Possible API issue.")
                return False
        
        logits_per_image = outputs.logits_per_image
        scores = logits_per_image.softmax(dim=1)  # Normalize scores

        # Get scores - first 4 are relevant, last 4 are irrelevant
        issue_score = max(scores[0][:4]).item()
        unrelated_score = max(scores[0][4:]).item()

        print(f"[DEBUG] CLIP relevance score: {issue_score}, Unrelated Score: {unrelated_score}")

        # Stricter thresholds for relevance
        if issue_score > 0.75 and (issue_score - unrelated_score) > 0.40:
            return True
        elif issue_score > 0.85:  # Very high relevance overrides difference threshold
            return True
            
        print(f"[INFO] Image rejected. Relevance: {issue_score:.2f}, Unrelated: {unrelated_score:.2f}")
        return False
            
    except Exception as e:
        print(f"[ERROR] Image relevance check failed: {e}")
        return False
    

def is_nsfw(image):
    """Detects NSFW content in an uploaded image."""
    try:
        from transformers import AutoModelForImageClassification, AutoImageProcessor
        from PIL import Image
         # Load models inside the function
        nsfw_processor = AutoImageProcessor.from_pretrained("google/vit-base-patch16-224")
        nsfw_model = AutoModelForImageClassification.from_pretrained("google/vit-base-patch16-224")
        
        image = Image.open(image)  # Open image from uploaded file
        inputs = nsfw_processor(images=image, return_tensors="pt")
        outputs = nsfw_model(**inputs)
        logits = outputs.logits
        predicted_label = logits.argmax().item()

        if predicted_label in [0, 1]:  # Assuming NSFW labels correspond to 0 and 1
            print("[WARNING] NSFW content detected. Upload rejected.")
            return True  
        
        return False  

    except Exception as e:
        print("[ERROR] NSFW detection failed:", e)
        return True  # Assume NSFW if an error occurs to prevent inappropriate uploads




def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        #email = request.POST["email"]
        password1 = request.POST["password1"]
        password2 = request.POST["password2"]

        if password1 != password2:
            messages.error(request, "Passwords do not match!")
            return redirect("register")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken!")
            return redirect("register")

        user = User.objects.create_user(username=username, password=password1)
        user.save()
        messages.success(request, "Registration successful! You can now log in.")
        return redirect("login")

    return render(request, "reports/register.html")


# User login view
def user_login(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        if user is not None:
            if user.is_superuser:  # 🚨 Prevent admin login here
                messages.error(request, "Admins must log in via the admin panel!")
                return redirect("login")  # You could also redirect to a custom admin login page
            login(request, user)
            return redirect("issue_list")  # Redirect to the page where the user can view issues
        else:
            messages.error(request, "Account not found or invalid credentials")
            return redirect("login")  # Keep the user on the login page to retry

    return render(request, "reports/login.html")

# User logout view
def user_logout(request):
    logout(request)
    return redirect('issue_list')  # Redirect to issue list instead of login page

# User issues view - displays issues reported by the logged-in user or anonymous users
def user_issues(request):
    if request.user.is_authenticated:
        issues = Issue.objects.filter(user=request.user)  # Only get issues where user matches
        return render(request, 'reports/user_issues.html', {'issues': issues})
    else:
        issues = Issue.objects.filter(user__isnull=True)  # Get issues reported by anonymous users
        return render(request, 'reports/user_issues.html', {'issues': issues})

# View for displaying all issues (for admins or anyone)
def view_issues(request):
    issues = Issue.objects.all().order_by('-created_at')  # Fetch all issues sorted by latest
    return render(request, 'reports/view_issues.html', {'issues': issues})

def home_view(request):
    # Get all issues
    issues = Issue.objects.all()

    # Prepare map data
    issues_json = json.dumps([
        {
            'title': issue.title,
            'description': issue.description,
            'status': issue.status,
            'location': issue.location,
            'lat': issue.lat,
            'lng': issue.lng
        } for issue in issues
    ])

    # Time ranges
    today = now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    year_ago = today - timedelta(days=365)

    def get_counts(since):
        return Issue.objects.filter(created_at__gte=since).values('status').annotate(count=Count('status'))

    analytics = {
        "week": list(get_counts(week_ago)),
        "month": list(get_counts(month_ago)),
        "year": list(get_counts(year_ago))
    }

    return render(request, 'home.html', {
    'issues_json': json.dumps(issues),
    'analytics_json': json.dumps(analytics)  # This must exist
})

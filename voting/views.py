from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Count
from django.db import IntegrityError
from django.contrib import messages
from django.contrib.auth import login as auth_login, logout as auth_logout, authenticate
from django.urls import reverse_lazy, reverse
from django.contrib.auth.views import LoginView
from django.views.generic import TemplateView
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from decouple import config
from django.http import HttpResponseBadRequest

from .models import Position, Contestant, Vote, Student, ElectionSettings
from .forms import RegisterForm
from django.contrib.auth.forms import AuthenticationForm  # Import AuthenticationForm
from .forms import  AccessCodeForm
from .models import Vote, Student
from .forms import ResetAllForm, PositionForm, ContestantForm



from .models import Student
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from .forms import PasswordResetForm

from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import PasswordResetForm
from .models import Student

def reset_password(request):
    if request.method == 'POST':
        form = PasswordResetForm(request.POST)

        if form.is_valid():
            reg_number = form.cleaned_data.get('reg_number')
            new_password = form.cleaned_data.get('new_password1')

            try:
                student = Student.objects.get(reg_number=reg_number)
                student.set_password(new_password)  # Hashes the password
                student.save()

                messages.success(request, 'Your password has been successfully updated!')
                return redirect('login')
            except Student.DoesNotExist:
                messages.error(request, 'User with this registration number does not exist.')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PasswordResetForm()

    return render(request, 'voting/reset_password.html', {'form': form})





def manage_positions(request):
    if request.method == 'POST':
        # Handle position deletion
        delete_position_id = request.POST.get('delete_position_id')
        if delete_position_id:
            position = get_object_or_404(Position, id=delete_position_id)
            position.delete()
            messages.success(request, 'Position deleted successfully.')
            return redirect('manage_positions')  # Refresh the page after deletion

        # Handle position addition
        form = PositionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Position added successfully.')
            return redirect('manage_positions')  # Refresh the page after addition
    else:
        form = PositionForm()

    positions = Position.objects.all()
    return render(request, 'voting/manage_positions.html', {'form': form, 'positions': positions})





# View to add contestants
def add_contestant(request):
    if request.method == 'POST':
        form = ContestantForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('list_contestants')  # Redirect to contestant list or another page
    else:
        form = ContestantForm()

    return render(request, 'voting/add_contestant.html', {'form': form})







# View to delete contestants
def delete_contestant(request, contestant_id):
    contestant = get_object_or_404(Contestant, id=contestant_id)
    contestant.delete()
    messages.success(request, 'Contestant deleted successfully.')
    return redirect('list_contestants')





# List contestants

def list_contestants(request):
    contestants = Contestant.objects.all()
    return render(request, 'voting/list_contestants.html', {'contestants': contestants})





def enter_access_code(request):
    next_url = request.POST.get('next') or request.GET.get('next') or 'list_students'
    if request.method == 'POST':
        form = AccessCodeForm(request.POST)
        if form.is_valid():
            access_code = form.cleaned_data.get('access_code')
            if access_code == ACCESS_CODE:
                request.session['has_access'] = True  # Set session variable
                return redirect(next_url)
            else:
                messages.error(request, 'Invalid access code.')
    else:
        form = AccessCodeForm()
    return render(request, 'voting/security.html', {'form': form, 'next': next_url})


def election_control(request):
    if not request.session.get('has_access'):
        return redirect(f"{reverse('enter_access_code')}?next=election_control")

    election = ElectionSettings.get_solo()

    if request.method == 'POST':
        election.is_open = not election.is_open
        election.save()
        messages.success(
            request,
            f"Voting is now {'OPEN — students can log in and vote.' if election.is_open else 'CLOSED — students can no longer log in or vote.'}"
        )
        return redirect('election_control')

    return render(request, 'voting/election_control.html', {'election': election})



def list_students(request):
    if not request.session.get('has_access'):
        return redirect('enter_access_code')

    if request.method == 'POST':
        student_id = request.POST.get('delete_student_id')
        if student_id:
            student = get_object_or_404(Student, id=student_id)
            student.delete()
            messages.success(request, 'Student deleted successfully.')
            return redirect('list_students')

    students = Student.objects.all()
    students_by_year = {}
    student_count_by_year = {}

    for student in students:
        year = student.reg_number[:4]  # Assuming reg starts with year
        if year not in students_by_year:
            students_by_year[year] = []
            student_count_by_year[year] = 0
        students_by_year[year].append(student)
        student_count_by_year[year] += 1

    total_students = students.count()
    largest_group_size = max(student_count_by_year.values(), default=0)  # 👈 NEW

    return render(request, 'voting/list_students.html', {
        'students_by_year': students_by_year,
        'student_count_by_year': student_count_by_year,
        'total_students': total_students,
        'largest_group_size': largest_group_size,  # 👈 pass to template
    })



def clear_admin_access(request):
    request.session.pop('has_access', None)  # Clear the session variable
    return redirect('enter_access_code')  # Redirect to the access code page






def reset_all(request):
    if request.method == 'POST':
        form = ResetAllForm(request.POST)
        if form.is_valid():
            entered_code = form.cleaned_data.get('access_code')

            # Check if the access code matches
            if entered_code != ACCESS_CODE:
                messages.error(request, 'Invalid access code. Please try again.')
                return redirect('reset_all')

            # Check if reset is confirmed
            if form.cleaned_data.get('confirm_reset'):
                # Reset all votes and contestants
                Vote.objects.all().delete()  # Delete all votes
                # Contestant.objects.all().delete()  # Delete all contestants
                messages.success(request, 'All votes and contestants have been reset.')
            else:
                messages.error(request, 'You must confirm the reset.')

            return redirect('reset_all')
    else:
        form = ResetAllForm()

    return render(request, 'voting/reset_vote.html', {'form': form})






ACCESS_CODE = config('ELECTION_ACCESS_CODE', default='BMEFUTO')  # Set your access code {this is for live count and vote reseting}

def live_vote_count(request):
    if request.method == 'POST':
        access_code = request.POST.get('access_code')
        if access_code == ACCESS_CODE:
            vote_data = {}
            positions = Position.objects.all()

            for position in positions:
                contestants = Contestant.objects.filter(position=position).annotate(vote_count=Count('vote'))
                vote_data[position] = contestants

            total_voters = Vote.objects.values('student').distinct().count()  # Count unique students who have voted

            return render(request, 'voting/live_vote_count.html', {
                'vote_data': vote_data,
                'total_voters': total_voters
            })
        else:
            messages.error(request, 'Invalid access code. Please try again.')

    return render(request, 'voting/live_vote_count.html')










def register_student(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            student = form.student
            student.set_password(form.cleaned_data['password1'])
            student.save()
            messages.success(
                request,
                f"Welcome, {student.full_name}! Your account is ready — you can now log in and vote."
            )
            return redirect('login')
    else:
        form = RegisterForm()
    return render(request, 'voting/register_student.html', {'form': form})





class BmeLoginView(LoginView):
    template_name = 'voting/login.html'
    form_class = AuthenticationForm  # Use AuthenticationForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['election_open'] = ElectionSettings.get_solo().is_open
        return context

    def form_valid(self, form):
        if not ElectionSettings.get_solo().is_open:
            form.add_error(None, 'Voting is currently closed. Please check back later.')
            return self.form_invalid(form)

        reg_number = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password')
        student = authenticate(reg_number=reg_number, password=password)

        if student is not None:
            auth_login(self.request, student)
            self.request.session['reg_number'] = reg_number
            return super().form_valid(form)
        else:
            form.add_error(None, 'Invalid registration number or password.')
            return self.form_invalid(form)

    def get_success_url(self):
        reg_number = self.request.session.get('reg_number')

        if reg_number:
            student = Student.objects.filter(reg_number=reg_number).first()

            if student:
                total_positions = Position.objects.count()
                voted_positions = Vote.objects.filter(student=student).values('position').distinct().count()

                if voted_positions == total_positions:
                    return reverse_lazy('completed')
                else:
                    remaining_position = Position.objects.exclude(
                        id__in=Vote.objects.filter(student=student).values_list('position_id', flat=True)
                    ).order_by('importance').first()

                    if remaining_position:
                        return reverse_lazy('vote_position', kwargs={'position_id': remaining_position.id})
                    else:
                        return reverse_lazy('completed')
            else:
                return reverse_lazy('login')
        else:
            return reverse_lazy('login')







def vote_position(request, position_id):
    reg_number = request.session.get('reg_number')

    if not reg_number:
        return redirect('login')

    if not ElectionSettings.get_solo().is_open:
        return render(request, 'voting/error.html', {
            'message': 'Voting has been closed by the department. Thank you for your interest.'
        })

    student = get_object_or_404(Student, reg_number=reg_number)
    position = get_object_or_404(Position, id=position_id)

    # Already voted for this position (fresh page load, e.g. a stale/back-navigated
    # ballot, or a resumed session) — just move on instead of showing a stale form.
    if request.method == 'GET' and Vote.objects.filter(student=student, position=position).exists():
        return redirect('next_position', position_id=position_id)

    if request.method == 'POST':
        # A network drop can make the browser retry an already-successful vote.
        # Treat "already voted for this position" as success and move forward
        # instead of dead-ending on an error page.
        if Vote.objects.filter(student=student, position=position).exists():
            return redirect('next_position', position_id=position_id)

        contestant_id = request.POST.get('contestant')

        if not contestant_id:
            return HttpResponseBadRequest("You must select a contestant.")

        contestant = get_object_or_404(Contestant, id=contestant_id, position=position)

        try:
            Vote.objects.create(student=student, position=position, contestant=contestant)
        except IntegrityError:
            # Two near-simultaneous submits both passed the check above —
            # the vote is recorded either way, so just continue.
            pass
        return redirect('next_position', position_id=position_id)

    contestants = Contestant.objects.filter(position=position)
    return render(request, 'voting/vote_position.html', {'position': position, 'contestants': contestants})


def site_map(request):
    return render(request, 'voting/site_map.html')






def next_position(request, position_id):
    reg_number = request.session.get('reg_number')

    if not reg_number:
        return redirect('login')

    student = get_object_or_404(Student, reg_number=reg_number)
    voted_positions = Vote.objects.filter(student=student).values_list('position_id', flat=True)
    all_positions = Position.objects.all().order_by('importance')
    remaining_positions = all_positions.exclude(id__in=voted_positions)

    if remaining_positions.exists():
        next_position = remaining_positions.first()
        return redirect('vote_position', position_id=next_position.id)
    else:
        return redirect('completed')








@login_required
@staff_member_required
def admin_dashboard(request):
    if not request.user.is_superuser:
        return redirect('login')

    total_votes = Vote.objects.count()
    total_students = Student.objects.count()
    total_positions = Position.objects.count()
    total_contestants = Contestant.objects.count()

    context = {
        'total_votes': total_votes,
        'total_students': total_students,
        'total_positions': total_positions,
        'total_contestants': total_contestants,
    }

    return render(request, 'voting/admin_dashboard.html', context)


class CompletedView(TemplateView):
    template_name = 'voting/completed.html'

    def get(self, request, *args, **kwargs):
        # Clear the voter's session once they're done so a shared/public
        # device doesn't stay logged in as the last person who voted.
        if request.user.is_authenticated:
            auth_logout(request)
        return super().get(request, *args, **kwargs)
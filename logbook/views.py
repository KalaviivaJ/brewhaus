from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import login
from django.contrib import messages
from django.db import connection
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import Batch, UserProfile

import logging
from django.dispatch import receiver
from django.contrib.auth.signals import user_login_failed


def register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already taken.')
            return render(request, 'logbook/register.html')

        # FIX for Identification and Authentication Failures
        # This view never validates password strength before creating
        # the account. Django ships with AUTH_PASSWORD_VALIDATORS in
        # settings.py (minimum length, common-password checks, etc.),
        # but those validators are only enforced automatically through
        # Django's own admin/forms, a custom view like this one must
        # call them explicitly, or they are silently skipped. As written,
        # a user can register with a password like "1" or "password",
        # making their account trivially easy to brute-force or guess.
        # The fix is to validate the password before creating the user:
        #
        #try:
            #validate_password(password)
        #except ValidationError as e:
            #for error in e.messages:
                #messages.error(request, error)
            #return render(request, 'logbook/register.html')

        user = User.objects.create_user(username=username, password=password)

        # FIX for Cryptographic Failures :
        # Storing the raw password anywhere outside Django's built-in,
        # securely-hashed `password` field is a serious vulnerability.
        # If this table were ever leaked (DB breach, backup exposure, a
        # developer with read access, etc.), every user's real password
        # would be immediately exposed in plaintext. The line below
        # should simply not exist — Django's create_user() call above
        # already stores the password correctly, salted and hashed.
        UserProfile.objects.create(user=user, plaintext_password=password)

        login(request, user)
        return redirect('batch_list')

    return render(request, 'logbook/register.html')


@login_required
def batch_list(request):
    batches = Batch.objects.filter(owner=request.user).order_by('-created_at')
    return render(request, 'logbook/batch_list.html', {'batches': batches})


@login_required
def add_batch(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        sugar_kg = float(request.POST.get('sugar_kg'))
        volume_l = float(request.POST.get('volume_l'))
        notes = request.POST.get('notes', '')

        Batch.objects.create(
            owner=request.user,
            name=name,
            sugar_kg=sugar_kg,
            volume_l=volume_l,
            notes=notes,
        )
        return redirect('batch_list')

    return render(request, 'logbook/add_batch.html')


@login_required
def view_batch(request, batch_id):
  #Fix for broken access control:
#Only let users access batches that belong to them.
#Otherwise, someone could change the batch_id in the URL
#to view another user's batch.
#batch = get_object_or_404(Batch, pk=batch_id, owner=request.user)

    batch = get_object_or_404(Batch, pk=batch_id)
    return render(request, 'logbook/view_batch.html', {'batch': batch})


@login_required
def search_batches(request):
    query = request.GET.get('q', '')
    results = []

    if query:
        # VULNERABLE Injection:
        # The code below concatenates user input directly into a raw SQL
        # string. An attacker can inject SQL through the search
        # box e.g. searching for:
        #   ' UNION SELECT id, username, password, 1, 1, 1 FROM auth_user --
        # can leak other tables' data, or a payload like
        #   ' OR '1'='1
        # can bypass the owner filter entirely, exposing every user's
        # batches regardless of who is logged in.

        with connection.cursor() as cursor:
            sql = "SELECT id, name, sugar_kg, volume_l, notes, created_at FROM logbook_batch WHERE owner_id = %d AND name LIKE '%%%s%%'" % (request.user.id, query)
            cursor.execute(sql)
            rows = cursor.fetchall()
            results = [
                {'id': r[0], 'name': r[1], 'sugar_kg': r[2], 'volume_l': r[3], 'notes': r[4], 'created_at': r[5]}
                for r in rows
            ]

        # FIX: use Django's ORM, which automatically parameterizes the
        # query, so user input is always treated as data, never as SQL.
        # batch_results = Batch.objects.filter(owner=request.user, name__icontains=query)
        # results = [
        #     {'id': b.id, 'name': b.name, 'sugar_kg': b.sugar_kg, 'volume_l': b.volume_l, 'notes': b.notes, 'created_at': b.created_at}
        #     for b in batch_results
        # ]

    return render(request, 'logbook/search.html', {'results': results, 'query': query})

#ogger = logging.getLogger('logbook.security')


# FIX for Security Logging and Monitoring Failures
# Without this signal receiver, failed login attempts are never
# recorded anywhere. An attacker could attempt hundreds or thousands
# of password guesses (a brute-force or credential-stuffing attack)
# and an administrator reviewing the server logs would see nothing
# unusual at all 
# The fix is to log every failed login attempt, including the
# attempted username and the source IP, so repeated failures from
# the same IP/username can be noticed and investigated.
#
#@receiver(user_login_failed)
#def log_failed_login(sender, credentials, request, **kwargs):
    #ip = request.META.get('REMOTE_ADDR', 'unknown') if request else 'unknown'
    #attempted_username = credentials.get('username', 'unknown')
    #logger.warning(
        #f"Failed login attempt for username='{attempted_username}' from IP={ip}"
    #)


    
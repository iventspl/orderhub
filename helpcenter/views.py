from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from .forms import HelpTicketForm, HelpTicketReplyForm
from django.contrib import messages
from django.http import JsonResponse
import json
from django.conf import settings
from django.db.models import Q
from .models import HelpCenterTicket, HelpCenterTicketHistory, HelpCenterTicketReply
from users.models import Membership, UserProfile, Department
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from users.models import User

@login_required
def help_center_dashboard(request, no_rows=10, page=1):

    assignees_choices = UserProfile.objects.filter(active_company=request.user.profile.active_company, assigned_role__in=['ASSIGNEE', 'ADMIN', 'MANAGER']).select_related('department').order_by('user__username')
    departments = HelpCenterTicket.Department.choices
    tickets = HelpCenterTicket.objects.filter(company=request.user.profile.active_company).order_by('-created_on')
    assignees = User.objects.filter(profile__active_company=request.user.profile.active_company, profile__assigned_role__in=['ASSIGNEE', 'ADMIN', 'MANAGER']).select_related('profile__department').order_by('username')

    # get all the query parameters for filtering, searching, and sorting
    sort_by = request.GET.get('sort_by')
    sort_direction = request.GET.get('sort_direction')
    search_query = request.GET.get('search_query')
    filter_department = request.GET.get('filter_department')
    filter_status = request.GET.get('filter_status')
    filter_assignee = request.GET.get('filter_assignee')

   

    # search query
    if search_query:
        tickets = tickets.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(created_by__username__icontains=search_query) |
            Q(assigned_to__username__icontains=search_query) |
            Q(ticket_number__icontains=search_query)
        )

    # filter by department
    if filter_department and filter_department != 'all':
        tickets = tickets.filter(department=filter_department)
    elif filter_department == 'all':
        tickets = tickets.filter(department__in=[choice[0] for choice in departments])

    # filter by status
    if filter_status and filter_status != 'all':
        tickets = tickets.filter(status=filter_status)
    elif filter_status == 'all':
        tickets = tickets.filter(status__in=[choice[0] for choice in HelpCenterTicket.TicketStatus.choices])

    # filter by assignee
    if filter_assignee and filter_assignee != 'all':
        if filter_assignee == 'unassigned':
            tickets = tickets.filter(assigned_to__isnull=True)
        else:
            tickets = tickets.filter(assigned_to__id=filter_assignee)
    elif filter_assignee == 'all':
        tickets = tickets.filter(assigned_to__in=assignees)

    # sort by
    if sort_by:
        if sort_direction == 'desc':
            tickets = tickets.order_by(f'-{sort_by}')
        else:
            tickets = tickets.order_by(sort_by)

     # pagination
    no_rows = int(request.GET.get('no_rows', 10))

    paginator = Paginator(tickets, no_rows)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    open_tickets = tickets.filter(status=HelpCenterTicket.TicketStatus.OPEN)
    in_progress_tickets = tickets.filter(status=HelpCenterTicket.TicketStatus.IN_PROGRESS)
    resolved_tickets = tickets.filter(Q(status=HelpCenterTicket.TicketStatus.RESOLVED) | Q(status=HelpCenterTicket.TicketStatus.CLOSED))
    unassigned_tickets = tickets.filter(assigned_to__isnull=True)

    context = {
        'page': 'helpcenter',
        'form': HelpTicketForm(),
        'form_reply': HelpTicketReplyForm(),
        'tickets': tickets,
        'assignees': assignees,
        'no_rows': no_rows,
        'page_obj': page_obj,
        'departments': departments,
        'status_choices': HelpCenterTicket.TicketStatus.choices,
        'assignee_choices': assignees_choices,
        'open_tickets': open_tickets,
        'in_progress_tickets': in_progress_tickets,
        'resolved_tickets': resolved_tickets,
        'unassigned_tickets': unassigned_tickets,
    }
    return render(request, 'helpcenter/help_center_dashboard.html', context)


@login_required
@require_POST
def submit_ticket(request):
    form = HelpTicketForm(request.POST)
    if form.is_valid():
        ticket = form.save(commit=False)
        ticket.created_by = request.user
        ticket.company = request.user.profile.active_company
        ticket.save()
        HelpCenterTicketHistory.objects.create(
            ticket=ticket,
            action='Ticket created',
            performed_by=request.user,
            company=request.user.profile.active_company
        )
        messages.success(request, 'Your ticket has been submitted successfully.')
    else:
        messages.error(request, 'There was an error submitting your ticket. Please check the form and try again.')
    return redirect('helpcenter:help_center_dashboard')


@login_required
@require_POST
def submit_ticket_reply(request, ticket_id):
    ticket = HelpCenterTicket.objects.get(id=ticket_id)
    form = HelpTicketReplyForm(request.POST)
    if form.is_valid():
        reply = form.save(commit=False)
        reply.ticket = ticket
        reply.commented_by = request.user
        reply.company = request.user.profile.active_company
        reply.save()
        HelpCenterTicketHistory.objects.create(
            ticket=ticket,
            action='Reply added',
            performed_by=request.user,
            company=request.user.profile.active_company
        )
        messages.success(request, 'Your reply has been added successfully.')
    else:
        messages.error(request, 'There was an error adding your reply. Please check the form and try again.')
    return redirect('helpcenter:help_center_dashboard')

@login_required
@require_POST
def update_ticket_status(request, ticket_id):
    ticket = HelpCenterTicket.objects.get(id=ticket_id)
    data = json.loads(request.body.decode('utf-8')) if request.body else {}
    new_status = data.get('status')
    if new_status:
        if ticket.assigned_to is None:
            return JsonResponse({'ok': False, 'message': 'Cannot change status of an unassigned ticket.'}, status=400)
        else:
            ticket.status = new_status
            ticket.save()
            HelpCenterTicketHistory.objects.create(
                ticket=ticket,
                action=f'Status changed to {new_status}',
                performed_by=request.user,
                company=request.user.profile.active_company
            )
            messages.success(request, 'Status updated successfully.')
            return JsonResponse({'ok': True, 'message': 'Status updated successfully.'})
    else:
        messages.error(request, 'Invalid status provided.')
        return JsonResponse({'ok': False, 'message': 'Invalid status provided.'}, status=400)
    

@login_required
@require_POST
def update_ticket_assignee(request, ticket_id, assignee_id):
    ticket = HelpCenterTicket.objects.get(id=ticket_id)
    data = json.loads(request.body.decode('utf-8')) if request.body else {}
    new_assignee_id = assignee_id
    if new_assignee_id:
        if new_assignee_id == "unassigned":
            ticket.assigned_to = None
            action_message = 'Assignee removed'
        else:
            new_assignee = UserProfile.objects.get(user__id=new_assignee_id)
            ticket.assigned_to = new_assignee.user
            action_message = f'Assignee changed to {new_assignee.get_full_name() or new_assignee.user.username}'
        ticket.save()
        HelpCenterTicketHistory.objects.create(
            ticket=ticket,
            action=action_message,
            performed_by=request.user,
            company=request.user.profile.active_company
        )
        messages.success(request, 'Assignee updated successfully.')
        return JsonResponse({'ok': True, 'message': 'Assignee updated successfully.'})
    else:
        messages.error(request, 'Invalid assignee provided.')
        return JsonResponse({'ok': False, 'message': 'Invalid assignee provided.'}, status=400)
    


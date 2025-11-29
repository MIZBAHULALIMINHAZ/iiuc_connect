from .models import GuestUser

def delete_guests_for_event(event_id):
    """
    Delete all guest users assigned to a specific event.
    """
    guests = GuestUser.objects(events__in=[str(event_id)])
    count = guests.count()
    guests.delete()
    return count

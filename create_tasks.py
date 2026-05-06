"""
Task Creator
Pushes action items extracted from emails to Google Tasks.
"""

import datetime

from gmail_reader import get_tasks_service


def create_tasks(action_items: list, email: dict) -> list:
    """
    Create a Google Task for each action item from a classified email.

    Args:
        action_items: list of action item strings from the classifier
        email:        the original email dict (used for task notes/context)

    Returns:
        list of created task dicts with 'id' and 'title'
    """
    service = get_tasks_service()
    created = []

    for item in action_items:
        task_body = {
            "title": item,
            "notes": f"From: {email['sender']}\nSubject: {email['subject']}",
        }

        task = service.tasks().insert(
            tasklist="@default",
            body=task_body,
        ).execute()

        created.append({"id": task["id"], "title": task["title"]})

    return created

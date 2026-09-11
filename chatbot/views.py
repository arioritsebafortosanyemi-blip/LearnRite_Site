import json
import logging

from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from store.models import Book, BookPrice
from store.utils import get_book_price

from orders.models import Order

from chatbot.claude_client import get_client
from chatbot.context_builder import build_system_prompt

logger = logging.getLogger(__name__)

MAX_MESSAGE_LENGTH = 2000
MAX_HISTORY_MESSAGES = 20
MAX_TOOL_ROUNDS = 4

TOOLS = [
    {
        "name": "get_order_status",
        "description": "Look up the status of the current customer's own order by its reference number, e.g. LR-ABC12345.",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_reference": {"type": "string", "description": "The order reference, e.g. LR-ABC12345"},
            },
            "required": ["order_reference"],
        },
    },
    {
        "name": "get_book_price",
        "description": "Look up the real price of a specific book for the current customer's account type and location. Only returns a price for logged-in institution accounts with pricing set for their tier.",
        "input_schema": {
            "type": "object",
            "properties": {
                "book_title": {"type": "string", "description": "The book's title, as close to the catalog title as possible"},
            },
            "required": ["book_title"],
        },
    },
]


def _serialize_block(block):
    if block.type == "text":
        return {"type": "text", "text": block.text}
    if block.type == "tool_use":
        return {"type": "tool_use", "id": block.id, "name": block.name, "input": block.input}
    return {"type": block.type}


def _execute_tool(tool_name, tool_input, user):
    if tool_name == "get_order_status":
        if not user.is_authenticated:
            return {"error": "The customer isn't logged in - ask them to log in and check their Order History page."}
        order_reference = (tool_input.get("order_reference") or "").strip()
        order = Order.objects.filter(order_reference__iexact=order_reference, user=user).first()
        if not order:
            return {"error": "No order with that reference was found on this customer's account."}
        return {
            "order_reference": order.order_reference,
            "status": order.get_status_display(),
            "total": str(order.total),
        }

    if tool_name == "get_book_price":
        if not user.is_authenticated:
            return {"error": "The customer isn't logged in, so no personalized price is available - direct them to log in, or contact us if they're an individual."}
        profile = getattr(user, "profile", None)
        if not profile or profile.account_type != BookPrice.AccountType.SCHOOL:
            return {"error": "This customer is an individual account - individuals never get online pricing, direct them to contact us by email regardless of order size."}
        book_title = (tool_input.get("book_title") or "").strip()
        book = Book.objects.filter(is_published=True, title__icontains=book_title).first()
        if not book:
            return {"error": f'No book matching "{book_title}" was found in the catalog.'}
        price = get_book_price(book, profile)
        if price is None:
            return {"error": f'"{book.title}" doesn\'t have a price set yet for this customer\'s account type/location - direct them to contact us to order it.'}
        return {
            "book_title": book.title,
            "price": str(price),
            "account_type": profile.get_account_type_display(),
            "location": profile.get_location_display(),
        }

    return {"error": "Unknown tool."}


@require_POST
def chat(request):
    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, TypeError):
        return JsonResponse({"error": "Invalid request."}, status=400)

    user_message = (body.get("message") or "").strip()
    history = body.get("history") or []

    if not user_message:
        return JsonResponse({"error": "Message is required."}, status=400)
    if len(user_message) > MAX_MESSAGE_LENGTH:
        return JsonResponse({"error": "Message is too long."}, status=400)
    if not isinstance(history, list):
        history = []
    history = history[-MAX_HISTORY_MESSAGES:]

    system_prompt = build_system_prompt()
    messages = history + [{"role": "user", "content": user_message}]
    client = get_client()

    try:
        response = client.messages.create(
            model=settings.CHATBOT_MODEL,
            max_tokens=1024,
            system=[{"type": "text", "text": system_prompt, "cache_control": {"type": "ephemeral"}}],
            tools=TOOLS,
            messages=messages,
        )
    except Exception:
        logger.exception("Chatbot request failed")
        return JsonResponse({"error": "The chatbot is temporarily unavailable. Please try again shortly."}, status=503)

    rounds = 0
    while response.stop_reason == "tool_use" and rounds < MAX_TOOL_ROUNDS:
        rounds += 1
        tool_use_blocks = [block for block in response.content if block.type == "tool_use"]
        messages.append({"role": "assistant", "content": [_serialize_block(b) for b in response.content]})

        tool_results = [
            {
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": json.dumps(_execute_tool(block.name, block.input, request.user)),
            }
            for block in tool_use_blocks
        ]
        messages.append({"role": "user", "content": tool_results})

        try:
            response = client.messages.create(
                model=settings.CHATBOT_MODEL,
                max_tokens=1024,
                system=[{"type": "text", "text": system_prompt, "cache_control": {"type": "ephemeral"}}],
                tools=TOOLS,
                messages=messages,
            )
        except Exception:
            logger.exception("Chatbot follow-up request failed")
            return JsonResponse({"error": "The chatbot is temporarily unavailable. Please try again shortly."}, status=503)

    if response.stop_reason == "tool_use":
        final_text = "Sorry, I'm having trouble looking that up right now - please contact us directly at info@learnritepublishers.com."
    else:
        final_text = "".join(block.text for block in response.content if block.type == "text")
    messages.append({"role": "assistant", "content": final_text})

    return JsonResponse({"reply": final_text, "history": messages})

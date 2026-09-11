from store.models import Category

from chatbot.models import KnowledgeSection

SYSTEM_PROMPT_TEMPLATE = """You are the customer support assistant for LearnRite International Publishers, \
a Nigerian textbook publisher. Answer questions using the grounding information below. Be brief and friendly.

Two things you must NEVER state from memory or guess: a specific order's status, and a specific book's price. \
Always use the get_order_status or get_book_price tools for those - the number or status you say must come from \
the tool result, never invented. If a tool returns an error (e.g. not logged in, individual account, order not \
found), explain that plainly to the customer rather than making up an answer.

Individual (personal) accounts never get self-service pricing or checkout, regardless of order size - always \
direct them to contact us by email for pricing, even for one book. Only institution (school) accounts get \
online pricing and checkout.

Book categories currently on the site: {categories}

Grounding information:
{knowledge}
"""


def build_system_prompt():
    sections = KnowledgeSection.objects.all()
    if sections:
        knowledge = "\n\n".join(f"## {section.get_section_display()}\n{section.content}" for section in sections)
    else:
        knowledge = "(No grounding content has been added yet - answer generally and suggest contacting the office for specifics.)"

    categories = Category.objects.values_list("name", flat=True).distinct()
    category_list = ", ".join(categories) if categories else "none listed yet"

    return SYSTEM_PROMPT_TEMPLATE.format(categories=category_list, knowledge=knowledge)

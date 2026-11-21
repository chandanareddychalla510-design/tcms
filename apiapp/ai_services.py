
import json
from google import genai
from django.conf import settings


def get_gemini_client():
    api_key = settings.GEMINI_API_KEY

    if not api_key:
        raise ValueError("Gemini API key is not configured")

    return genai.Client(api_key=api_key)


def get_ai_response(prompt):
    client = get_gemini_client()

    response = client.interactions.create(
        model="gemini-3.5-flash-lite",
        input=prompt
    )

    if not response.output_text:
        raise ValueError("Gemini returned an empty response")

    return response.output_text.strip()


# ---------------------------------
# 1. AI TICKET CLASSIFICATION
# ---------------------------------

def classify_ticket(subject, description):
    prompt = f"""
    Analyze this customer support ticket.

    Subject: {subject}
    Description: {description}

    Return ONLY valid JSON with these fields:
    category: TECHNICAL, BILLING, ACCOUNT, or GENERAL
    priority: LOW, MEDIUM, HIGH, or URGENT
    reason: short explanation
    """

    result = get_ai_response(prompt)

    try:
        result = result.replace("```json", "").replace("```", "").strip()
        data = json.loads(result)

        if data.get("category") not in [
            "TECHNICAL", "BILLING", "ACCOUNT", "GENERAL"
        ]:
            raise ValueError("Invalid category")

        if data.get("priority") not in [
            "LOW", "MEDIUM", "HIGH", "URGENT"
        ]:
            raise ValueError("Invalid priority")

        return data

    except (json.JSONDecodeError, ValueError):
        raise ValueError("AI returned an invalid ticket classification")


# ---------------------------------
# 2. AI FAQ ANSWER GENERATION
# ---------------------------------

def generate_faq_answer(question, faq_context=""):
    prompt = f"""
    Answer the customer's question using the FAQ information below.

    FAQ information:
    {faq_context}

    Customer question:
    {question}

    If the FAQ information does not contain the answer,
    clearly say that customer support assistance is needed.
    Do not invent company policies.
    """

    return get_ai_response(prompt)


# ---------------------------------
# 3. AI AGENT REPLY SUGGESTION
# ---------------------------------

def suggest_agent_response(ticket_subject, customer_message):
    prompt = f"""
    Suggest a professional and helpful reply for a customer support agent.

    Ticket subject: {ticket_subject}
    Customer message: {customer_message}

    Do not claim that an issue is resolved unless the information confirms it.
    Return only the suggested reply.
    """

    return get_ai_response(prompt)


# ---------------------------------
# 4. AI CONVERSATION SUMMARY
# ---------------------------------

def summarize_conversation(messages):
    conversation = "\n".join(
        [
            f"{message.get('sender', 'User')}: {message.get('message', '')}"
            for message in messages
        ]
    )

    prompt = f"""
    Summarize this customer support conversation.

    Conversation:
    {conversation}

    Include:
    1. Customer's main issue
    2. Actions taken
    3. Current situation
    4. Pending actions

    Keep the summary concise.
    """

    return get_ai_response(prompt)


# ---------------------------------
# 5. PHASE 5 - AI AGENT WORKLOAD ANALYSIS
# ---------------------------------

def analyze_agent_workload(agent_data, unassigned_tickets):
    prompt = f"""
    You are an AI assistant for a Ticket Management System.

    Analyze the following agent workload information.

    AGENT DETAILS:
    {json.dumps(agent_data, indent=2)}

    UNASSIGNED TICKETS:
    {json.dumps(unassigned_tickets, indent=2)}

    Rules:
    1. Consider only AVAILABLE agents for new assignments.
    2. Prefer agents with lower active workload.
    3. Consider agent specialization and ticket category.
    4. Consider ticket priority.
    5. Do not recommend BUSY or OFFLINE agents for new assignments.
    6. Do not assign tickets automatically.
    7. If no suitable available agent exists, clearly mention that.

    Return ONLY valid JSON in this format:

    {{
        "analysis": "Overall workload analysis",
        "suggestions": [
            {{
                "ticket_id": 1,
                "ticket_number": "TECH-00001",
                "suggested_agent_id": 2,
                "suggested_agent": "agent1",
                "reason": "Reason for recommendation"
            }}
        ],
        "recommendation": "Final recommendation for admin"
    }}
    """

    result = get_ai_response(prompt)

    try:
        result = result.replace("```json", "").replace("```", "").strip()
        data = json.loads(result)

        if not isinstance(data, dict):
            raise ValueError("Invalid AI response")

        if not isinstance(data.get("suggestions"), list):
            raise ValueError("Suggestions must be a list")

        return data

    except (json.JSONDecodeError, ValueError):
        raise ValueError("AI returned invalid workload analysis")

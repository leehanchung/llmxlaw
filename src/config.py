from prompts import conversation_stages

VERBOSE = True
CONFIG = dict(
    legal_intaker_name = "AI",
    company_name="Stanford CodeX Hackathon",
    conversation_stage_dict=conversation_stages,
    conversation_purpose = """help generate a legal complaint that would be ready to file in civil court.""",
    conversation_history=[
        """'Hello, this is the Stanford CodeX Hackathon Legal Complaint Generator. Please tell me your name? <END_OF_TURN>'
        """,
    ],
    conversation_stage = conversation_stages.get(
        '1',
        (
            "Introduction: Start the conversation by introducing yourself and"
            "your company. Be polite and respectful while keeping the tone of"
            " the conversation professional. Do not ask how the user learned of your services. "
        )
    )
)

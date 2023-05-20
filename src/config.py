from prompts import conversation_stages

VERBOSE = True
CONFIG = dict(
    legal_intaker_name = "Michael Ross",
    company_name="Pearson Hardman",
    conversation_stage_dict=conversation_stages,
    conversation_purpose = "help generate a legal complaint that would be ready to file in civil court.",
    conversation_history=['Hello, this is the Stanford CodeX Legal Complaint Generator. Please tell me your name? <END_OF_TURN>'],
    conversation_type="call",
    conversation_stage = conversation_stages.get('1', "Introduction: Start the conversation by introducing yourself explaining that you are here to help generate a formal complaint. Be polite and respectful while keeping the tone of the conversation professional. Your greeting should be welcoming.")
)

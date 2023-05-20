from prompts import conversation_stages

VERBOSE = True
CONFIG = dict(
    legal_intaker_name = "Michael Ross",
    company_name="Pearson Hardman",
    conversation_stage_dict=conversation_stages,
    conversation_type="consulting interview",
    conversation_purpose = """
        find out whether they are looking to achieve better sleep via buying
        a premier mattress.
    """,
    conversation_history=[
        """Hello, this is Mike Ross from Pearson Hardman. How are you doing
        today? <END_OF_TURN>','User: I am well, howe are you?<END_OF_TURN>']
        """,
    ],
    conversation_stage = conversation_stages.get(
        '1',
        (
            "Introduction: Start the conversation by introducing yourself and"
            "your company. Be polite and respectful while keeping the tone of"
            " the conversation professional."
        )
    )
)

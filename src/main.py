import os


from typing import Dict, List, Any

from langchain import LLMChain, PromptTemplate
from langchain.llms import BaseLLM
from pydantic import BaseModel, Field
from langchain.chains.base import Chain
from langchain.chat_models import ChatOpenAI

from dotenv import load_dotenv
from prompts import (
    conversation_stages,
    stage_analyzer_inception_prompt_template,
    legal_agent_inception_prompt,
)
from config import VERBOSE

load_dotenv()
verbose=VERBOSE


class StageAnalyzerChain(LLMChain):
    """Chain to analyze which conversation stage should the conversation move into."""

    @classmethod
    def from_llm(cls, llm: BaseLLM, verbose: bool = True) -> LLMChain:
        """Get the response parser."""
        prompt = PromptTemplate(
            template=stage_analyzer_inception_prompt_template,
            input_variables=["conversation_history"],
        )
        return cls(prompt=prompt, llm=llm, verbose=verbose)


class LegalIntakeConversationChain(LLMChain):
    """Chain to generate the next utterance for the conversation."""

    @classmethod
    def from_llm(cls, llm: BaseLLM, verbose: bool = True) -> LLMChain:
        """Get the response parser."""
        prompt = PromptTemplate(
            template=legal_agent_inception_prompt,
            input_variables=[
                "legal_intaker_name",
                "company_name",
                "conversation_purpose",
                "conversation_type",
                "conversation_stage",
                "conversation_history"
            ],
        )
        return cls(prompt=prompt, llm=llm, verbose=verbose)

class LegalIntaker(Chain, BaseModel):
    """Controller model for the Sales Agent."""

    conversation_history: List[str] = []
    current_conversation_stage: str = '1'
    stage_analyzer_chain: StageAnalyzerChain = Field(...)
    sales_conversation_utterance_chain: LegalIntakeConversationChain = Field(...)
    conversation_stage_dict: Dict = {
        '1': "Introduction: Start the conversation by introducing yourself and your company. Be polite and respectful while keeping the tone of the conversation professional. Your greeting should be welcoming. Always clarify in your greeting the reason why you are contacting the prospect.",
        '2': "Qualification: Qualify the prospect by confirming if they are the right person to talk to regarding your product/service. Ensure that they have the authority to make purchasing decisions.",
        '3': "Value proposition: Briefly explain how your product/service can benefit the prospect. Focus on the unique selling points and value proposition of your product/service that sets it apart from competitors.",
        '4': "Needs analysis: Ask open-ended questions to uncover the prospect's needs and pain points. Listen carefully to their responses and take notes.",
        '5': "Solution presentation: Based on the prospect's needs, present your product/service as the solution that can address their pain points.",
        '6': "Objection handling: Address any objections that the prospect may have regarding your product/service. Be prepared to provide evidence or testimonials to support your claims.",
        '7': "Close: Ask for the sale by proposing a next step. This could be a demo, a trial or a meeting with decision-makers. Ensure to summarize what has been discussed and reiterate the benefits."
        }

    legal_intaker_name: str = "Ted Lasso"
    company_name: str = "Sleep Haven"
    conversation_type: str = "call"

    def retrieve_conversation_stage(self, key):
        return self.conversation_stage_dict.get(key, '1')
    
    @property
    def input_keys(self) -> List[str]:
        return []

    @property
    def output_keys(self) -> List[str]:
        return []

    def seed_agent(self):
        # Step 1: seed the conversation
        self.current_conversation_stage= self.retrieve_conversation_stage('1')
        self.conversation_history = []

    def determine_conversation_stage(self):
        conversation_stage_id = self.stage_analyzer_chain.run(
            conversation_history='"\n"'.join(self.conversation_history), current_conversation_stage=self.current_conversation_stage)

        self.current_conversation_stage = self.retrieve_conversation_stage(conversation_stage_id)
  
        print(f"Conversation Stage: {self.current_conversation_stage}")
        return conversation_stage_id
        
    def human_step(self, human_input):
        # process human input
        human_input = human_input + '<END_OF_TURN>'
        self.conversation_history.append(human_input)

    def step(self):
        self._call(inputs={})

    def _call(self, inputs: Dict[str, Any]) -> None:
        """Run one step of the sales agent."""

        # Generate agent's utterance
        ai_message = self.sales_conversation_utterance_chain.run(
            legal_intaker_name = self.legal_intaker_name,
            company_name=self.company_name,
            conversation_purpose = self.conversation_purpose,
            conversation_history="\n".join(self.conversation_history),
            conversation_stage = self.current_conversation_stage,
            conversation_type=self.conversation_type
        )
        
        # Add agent's response to conversation history
        self.conversation_history.append(ai_message)

        print(f'{self.legal_intaker_name}: ', ai_message.rstrip('<END_OF_TURN>'))
        return {}

    @classmethod
    def from_llm(
        cls, llm: BaseLLM, verbose: bool = False, **kwargs
    ) -> "LegalIntaker":
        """Initialize the LegalIntaker Controller."""
        stage_analyzer_chain = StageAnalyzerChain.from_llm(llm, verbose=verbose)
        sales_conversation_utterance_chain = LegalIntakeConversationChain.from_llm(
            llm, verbose=verbose
        )

        return cls(
            stage_analyzer_chain=stage_analyzer_chain,
            sales_conversation_utterance_chain=sales_conversation_utterance_chain,
            verbose=verbose,
            **kwargs,
        )

# Set up of your agent

# test the intermediate chains
llm = ChatOpenAI(temperature=0.0)

# Agent characteristics - can be modified
config = dict(
    legal_intaker_name = "Michael Ross",
    company_name="Pearson Hardman",
    conversation_purpose = "find out whether they are looking to achieve better sleep via buying a premier mattress.",
    conversation_history=['Hello, this is Ted Lasso from Sleep Haven. How are you doing today? <END_OF_TURN>','User: I am well, howe are you?<END_OF_TURN>'],
    conversation_type="call",
    conversation_stage = conversation_stages.get('1', "Introduction: Start the conversation by introducing yourself and your company. Be polite and respectful while keeping the tone of the conversation professional.")
)

legal_agent = LegalIntaker.from_llm(llm, verbose=False, **config)

# init sales agent
stage = 0
legal_agent.seed_agent()
while stage != 7:
    stage = legal_agent.determine_conversation_stage()
    legal_agent.step()
    foo = input("\n\n>> ")
    legal_agent.human_step(foo)


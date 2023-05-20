import os


from typing import Dict, List, Any

from langchain import LLMChain, PromptTemplate
from langchain.llms import BaseLLM
from pydantic import BaseModel, Field
from langchain.chains.base import Chain
from langchain.chat_models import ChatOpenAI

from dotenv import load_dotenv
from prompts import (
    stage_analyzer_inception_prompt_template,
    legal_agent_inception_prompt,
)
from config import CONFIG, VERBOSE

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
    conversation_stage_dict: Dict
    conversation_purpose: str
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

def main():
    llm = ChatOpenAI(temperature=0.0)
    legal_agent = LegalIntaker.from_llm(llm, verbose=False, **CONFIG)

    stage = 0
    legal_agent.seed_agent()
    while stage != 7:
        stage = legal_agent.determine_conversation_stage()
        legal_agent.step()
        foo = input("\n\n>> ")
        legal_agent.human_step(foo)
        stage = legal_agent.determine_conversation_stage()


if __name__ == "__main__":
    main()

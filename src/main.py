import os
import time
import json
import re
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
                "conversation_stage",
                "conversation_history"
            ],
        )
        return cls(prompt=prompt, llm=llm, verbose=verbose)

class LegalIntaker(Chain, BaseModel):
    """Controller model for the Legal Intaker Agent."""

    conversation_history: List[str] = []
    current_conversation_stage: str = '1'
    stage_analyzer_chain: StageAnalyzerChain = Field(...)
    sales_conversation_utterance_chain: LegalIntakeConversationChain = Field(...)
    conversation_stage_dict: Dict
    conversation_purpose: str
    legal_intaker_name: str
    company_name: str

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
        return conversation_stage_id
        
    def human_step(self, human_input):
        # process human input
        human_input = human_input + '<END_OF_TURN>'
        self.conversation_history.append(human_input)

    def step(self):
        stage = self._call(inputs={})
        return stage

    def _call(self, inputs: Dict[str, Any]) -> None:
        """Run one step of the sales agent."""

        # Generate agent's utterance
        ai_message = self.sales_conversation_utterance_chain.run(
            legal_intaker_name = self.legal_intaker_name,
            company_name=self.company_name,
            conversation_purpose = self.conversation_purpose,
            conversation_history="\n".join(self.conversation_history),
            conversation_stage = self.current_conversation_stage,
        )
        
        # Add agent's response to conversation history
        self.conversation_history.append(ai_message)

        print(f'{self.legal_intaker_name}: ', ai_message.rstrip('<END_OF_TURN>'))
        return self.current_conversation_stage

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

    stage = 1
    legal_agent.seed_agent()
    while True:
        stage = legal_agent.determine_conversation_stage()
        print(f"\n\nConversation Stage: {legal_agent.current_conversation_stage}\n\n")
        print(f"Current stage: {stage}")
        legal_agent.step()
        if "Exit" in legal_agent.current_conversation_stage:
            break
        # stage_id = legal_agent.determine_conversation_stage()

        user_input = input("\n\n>> ")
        stripped_input = user_input.replace('\n', '')

        # time.sleep(1)
        legal_agent.human_step(stripped_input.replace('\n', ''))

    with open('legal_complaint.md', 'w') as writer:
        writer.write('\n\n'.join(legal_agent.conversation_history))



    with open('legal_complaint.md', 'r') as file:
        content = file.read()

    # Use regex to find JSON (assumes your JSON starts and ends with {})
    json_string = re.search(r'{.*}', content, re.DOTALL).group()

    # Convert the JSON string to a Python dictionary
    data = json.loads(json_string)

    # Write the Python dictionary to a new JSON file
    with open('legal_complaint.json', 'w') as file:
        json.dump(data, file)


if __name__ == "__main__":
    main()

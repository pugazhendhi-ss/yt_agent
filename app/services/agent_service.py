from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate

from app.models.agent_model import ChatPayload
from app.templates.agent_prompt import agent_prompt

load_dotenv()

from langchain_openai import ChatOpenAI
from langchain.agents import create_openai_functions_agent, AgentExecutor
from langchain import hub
from app.services.memory_manager import MemoryManager
from app.services.yt_tool import fetch_video_transcript
from app.services.langsmith_manager import TracingManager


# Initialize the LLM
LLM = ChatOpenAI(model="gpt-4o-mini", temperature=0.02)

class Agent:

    def __init__(self, project_name: str = "youtube-agent"):
        self.tracing_manager = TracingManager(project_name)
        self.tools = [fetch_video_transcript]
        # self.prompt = hub.pull("hwchase17/openai-functions-agent")
        self.prompt = agent_prompt



    def chat(self, chat_data: ChatPayload) -> dict:

        try:
            langsmith_config = self.tracing_manager.get_config(chat_data.id)
            runnable_history_config = {"session_id": chat_data.id}
            config = {**langsmith_config, "configurable": runnable_history_config}


            prompt_template = ChatPromptTemplate.from_messages([
                ("system", self.prompt),
                ("user", "{chat_history}\n{input}"),
                ("system", "{agent_scratchpad}")
            ])
            # prompt_template = self.prompt

            agent = create_openai_functions_agent(llm=LLM, tools=self.tools, prompt=prompt_template)

            agent_executor = AgentExecutor(agent=agent,
                                           tools=self.tools,
                                           verbose=True,
                                           handle_parsing_errors=True,
                                           max_iterations=5)

            memory_wrapper  = MemoryManager(chat_data.id)
            agent_with_memory = memory_wrapper.wrap_with_memory(agent_executor)

            # Invoke the agent with user input and LangSmith trace config
            response = agent_with_memory.invoke({"input": chat_data.query}, config=config)
            return {"response": response["output"]}

        except Exception as e:
            return {"response": f"Sorry, I encountered an error: {str(e)}"}

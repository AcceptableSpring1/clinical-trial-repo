from dotenv import load_dotenv
from typing_extensions import TypedDict, Annotated
from langgraph.types import Send
from pinecone import Pinecone
from langchain.messages import AnyMessage
from langchain.messages import HumanMessage
from langgraph.graph import StateGraph, START, END
import operator
from openai import AsyncOpenAI 
import litellm

load_dotenv()
client = AsyncOpenAI()
litellm.success_callback = ["langfuse_otel"]
litellm.failure_callback = ["langfuse_otel"] 
pc = Pinecone()

class MessageState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]
    sub_question: list[str]
    results: Annotated[list[str],operator.add]
    llm_calls: int
    citation: Annotated[list[str],operator.add]
    synthesis: list[str]
    trial_id: str

async def decompose(state:dict):
    try:
        qsplit = await litellm.acompletion(
                model="bedrock/us.amazon.nova-lite-v1:0",
                messages =[
                {"role": "system", "content": "You receive a user question, if the question contains multiple distinct parts, return each part as a separate sub-question, one per line, nothing else. If the question is a single part, return it as-is on one line, nothing else. Never explain, never add context, only return the sub-questions. if the question is vague or unclear, return it as-is on one line rather than asking for clarification"},
                {"role":"user","content":state["messages"][-1].content}
                ]
        )
    except Exception as e:
        print(f"Decompose failed: {e}")
        return{
            "sub_question":["Error: could not process the question"]
        }


    return {
        "sub_question": [q for q in qsplit.choices[0].message.content.split('\n') if q.strip()],
        "llm_calls":state.get('llm_calls', 0) + 1
        }
        
async def retrieve(state:dict):
    async with pc.IndexAsyncio(host="https://clinical-trial-test-two-4pv7yax.svc.aped-4627-b74a.pinecone.io") as idx:
        try:
            response = await client.embeddings.create(
            input=state["sub_question"],
            model="text-embedding-3-small"
            )
            q_one = response.data[0].embedding
        except Exception as e:
            print(f"The embedding of the question failed: {e}")
            return{
                "results": ["Error: Issue processing the question"],
                "citation": []
            }
        try:
            the_query = await idx.query(
                namespace=state["trial_id"],
                vector=q_one, 
                top_k=3,
                include_metadata=True,
                include_values=False
        )
            pineresult = [x["metadata"]["text"] for x in the_query["matches"]]
            pine_citation = [x["id"] for x in the_query["matches"]]
            
        except Exception as e:
            print(f"Error during query: {e}")
            return{
                "results": ["Error during retrieval"],
                "citation": []
            }

        return{
            "results": pineresult,
            "citation": pine_citation
        }

async def synthesize(state:dict):
    if state.get('llm_calls', 0) >= 5:
        return {"synthesis": "Error: max LLM calls reached"}
    
    try:
        final = await litellm.acompletion(
            model="bedrock/us.amazon.nova-lite-v1:0",
            messages =[
            {"role":"system","content": "You are an agent that is going to receive answers a set of answers."
            "You are to combine these answers in an organized paragraph manner. No more than 8 sentences, and only english verbage in the answer no code"}, 
            {"role":"user","content": ' | '.join(state["results"])}
        ]
            
        )
    except Exception as e:
        print(f"Synthesis issue: {e}")
        return{
            "synthesis": ["Error: Problem with Synthesis"]
        }
    
   
    return{
        "synthesis": final.choices[0].message.content,
        "llm_calls": state.get('llm_calls',0) + 1
    }

def continue_decompose(state:MessageState):
     return[
        Send('retrieve', {"sub_question":q, "trial_id": state["trial_id"]}) for q in state["sub_question"]
     ]

    
    
agent_builder = StateGraph(MessageState)
agent_builder.add_node("decompose",decompose)
agent_builder.add_node("retrieve", retrieve)
agent_builder.add_node("synthesize", synthesize)

agent_builder.add_edge(START, "decompose")
agent_builder.add_conditional_edges("decompose",continue_decompose,["retrieve"])
agent_builder.add_edge("retrieve","synthesize")
agent_builder.add_edge("synthesize", END)

agent = agent_builder.compile()


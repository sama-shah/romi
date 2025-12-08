from dotenv import load_dotenv
import os
from openai import OpenAI
import json

load_dotenv()

conversation_history = [
    {"role": "system", "content": """You are a friendly and professional period-tracking assistant.
    Do not provide medical diagnoses. If the user asks 
    for medical advice, politely suggest consulting a healthcare professional. 
    Acknowledge user input respectfully and keep responses concise.
    - Analyze the user's message and fill in the following JSON template with relevant information.
    - return the message to the user in the message field of the JSON
    - Do not add extra fields or commentary; only return valid JSON.
    - "message" and "time of day" fields are strings, feeling is from 1-5 and the remainder are from 0-10 fill in based on context clues from their message and history of similar timeframe
    - JSON Template:
{
"message": ,
"time of day": ,
"feeling": ,
"hot flushes": ,
"sweating": ,
"trouble sleeping": ,
"muscle or joint pain": ,
"rapid heart beat": ,
"brain fog": ,
"forgetfulness": ,
"less sexual desire": ,
"dry vagina or painful sex": ,
"anxiety": ,
"itchy skin": ,
"tiredness": ,
"urinary problems": ,
"irregular periods": ,
"mood changes": ,
"weight gain": ,
}
Example output:
{
"message": "I am sorry to hear that. Sleep disruption is a common symptom. Can you tell me more? Were you experiencing night swets or hot flashs",
"time of day": "morning",
"feeling": 2,
"hot flushes": 4,
"sweating": 4,
"trouble sleeping": 7,
"muscle or joint pain": 0,
"rapid heart beat": 2,
"brain fog": 0,
"forgetfulness": 0,
"less sexual desire": 0,
"dry vagina or painful sex": 0,
"anxiety": 3,
"itchy skin": 0,
"tiredness": 7,
"urinary problems": 0,
"irregular periods": 0,
"mood changes": 3,
"weight gain": 0,
}
    
    -Always return valid JSON. Do not include any explanation outside of the JSON.
"""}
]
#NOTE THIS IS A TEMP JSON TEMPLATE AS WE ARE CHANGING THAT IN THE FRONT END

class ChatClient:
    def __init__(self, conversation_history, history_limit=3):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.conversation_history = conversation_history
        self.history_limit = history_limit

    def returnMessage(self, message):
        
        self.conversation_history.append({"role": "user", "content": message})
        
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages = self.conversation_history
        )
        assistant_reply = response.choices[0].message.content
        self.conversation_history.append({"role": "assistant", "content": assistant_reply})
        if len(self.conversation_history) > self.history_limit * 2 + 1:
            self.conversation_history = [self.conversation_history[0]] + self.conversation_history[-self.history_limit*2:]
            
        return assistant_reply
    
if __name__ == '__main__':
    chat_client = ChatClient(conversation_history)
    print(chat_client.returnMessage("Good morning! I didn’t sleep well last night and woke up feeling really tired. I also had some hot flushes and a bit of anxiety. My joints were a little sore too."))

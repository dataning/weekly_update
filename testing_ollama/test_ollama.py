from ollama import chat, ChatResponse

response: ChatResponse = chat(
    model='gemma3:27b-it-qat',
    messages=[
        { 'role': 'system', 'content': 'You are an AI assistant.' },
        { 'role': 'user',   'content': 'Where is York?'      },
    ],
)

# get the generated reply
print(response['message']['content'])

# Example Usage for Extract Info API

## Updated Message Structure

The API now accepts messages with the following structure:

```typescript
// Frontend Type (TypeScript)
interface Message {
    id?: string;
    text: string;
    audio?: string;
    lipsync?: Lipsync;
    facialExpression?: string;
    animation?: string;
    sender?: MessageSender;
}

// Backend Schema (Python/Pydantic)
class MessageInput(BaseModel):
    id: Optional[str] = None
    text: str
    sender: Optional[MessageSender] = None
```

## API Request Example

```json
{
  "messages": [
    {
      "id": "msg1",
      "text": "I need to book a flight to Tehran",
      "sender": "CLIENT"
    },
    {
      "id": "msg2", 
      "text": "What's your travel date and passenger information?",
      "sender": "AVATAR"
    },
    {
      "id": "msg3",
      "text": "I'm traveling on March 15th with 2 passengers. My name is Ali Reza and my wife is Fatemeh",
      "sender": "CLIENT"
    }
  ]
}
```

## API Response Example

```json
{
  "airportName": "Tehran Imam Khomeini International Airport",
  "travelDate": "March 15th",
  "flightNumber": "",
  "passengers": [
    {
      "fullName": "Ali Reza",
      "nationalId": "",
      "luggageCount": 0
    },
    {
      "fullName": "Fatemeh", 
      "nationalId": "",
      "luggageCount": 0
    }
  ]
}
```

## Frontend Usage Example

```typescript
const extractInfo = async (messages: Message[]) => {
  const response = await fetch('/api/extract-info', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      messages: messages.map(msg => ({
        id: msg.id,
        text: msg.text,
        sender: msg.sender
      }))
    })
  });
  
  return await response.json();
};
```

## Key Changes Made

1. **Updated Schema**: `ExtractInfoRequest` now uses `List[MessageInput]` instead of `list[dict]`
2. **Proper Type Safety**: Messages are now properly typed with Pydantic models
3. **Required Fields**: Only `id`, `text`, and `sender` are processed (other fields are ignored)
4. **Service Update**: The service now correctly accesses message properties using dot notation
5. **Route Update**: The route passes the entire request object to the service

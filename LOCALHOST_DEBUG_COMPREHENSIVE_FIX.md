# 🔧 Localhost Debug - Comprehensive Fix Applied

## 🎯 **Current Status**

I've applied comprehensive debugging and error handling to identify exactly what's happening when you try to use the application on localhost.

## 🔍 **Enhanced Debugging Added**

### **1. Socket Connection Logging**
```python
@socketio.on('connect')
def handle_connect():
    try:
        session_id = request.sid
        client_info = {
            "connected_at": datetime.now(),
            "message_count": 0,
            "user_agent": request.headers.get('User-Agent', 'Unknown'),
            "remote_addr": request.remote_addr
        }
        active_sessions[session_id] = client_info
        
        logger.info(f"✅ Client connected: {session_id} from {request.remote_addr}")
        logger.info(f"User-Agent: {request.headers.get('User-Agent', 'Unknown')}")
        
        # Send welcome message
        emit('bot_message', {
            "message": "👋 Welcome to the indici Reports Assistant! How can I help you today?",
            "timestamp": datetime.now().isoformat(),
            "type": "greeting"
        })
        
        logger.info(f"Welcome message sent to {session_id}")
        
    except Exception as e:
        logger.error(f"❌ Error in handle_connect: {e}")
        import traceback
        traceback.print_exc()
```

### **2. Message Processing Logging**
```python
@socketio.on('user_message')
def handle_user_message(data):
    try:
        session_id = request.sid
        message = data.get('message', '').strip()
        
        logger.info(f"📨 Received message from {session_id}: '{message}'")
        logger.info(f"Session info: {active_sessions.get(session_id, 'Unknown')}")
        
        # Show typing indicator
        emit('bot_typing', {"typing": True})
        logger.info(f"🔄 Typing indicator sent to {session_id}")
        
        # Process message asynchronously
        def process_message():
            try:
                logger.info(f"🔄 Starting async message processing for {session_id}")
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                # Handle the message
                logger.info(f"🤖 Calling chat_handler.handle_message...")
                response_data = loop.run_until_complete(
                    chat_handler.handle_message(message, session_id)
                )
                logger.info(f"✅ Chat handler response: {response_data}")
                
                loop.close()
                
                # Send response
                logger.info(f"📤 Sending response to {session_id}")
                socketio.emit('bot_typing', {"typing": False}, room=session_id)
                socketio.emit('bot_message', {
                    "message": response_data["response"],
                    "timestamp": response_data["timestamp"],
                    "type": response_data["type"],
                    "success": response_data["success"]
                }, room=session_id)
                logger.info(f"✅ Response sent successfully to {session_id}")
                
            except Exception as e:
                logger.error(f"❌ Error processing message for {session_id}: {str(e)}")
                import traceback
                traceback.print_exc()
                
                socketio.emit('bot_typing', {"typing": False}, room=session_id)
                socketio.emit('bot_message', {
                    "message": "❌ Sorry, I encountered an error processing your message. Please try again.",
                    "timestamp": datetime.now().isoformat(),
                    "type": "error",
                    "success": False
                }, room=session_id)
                logger.info(f"Error message sent to {session_id}")
        
        # Start processing in background thread
        import threading
        thread = threading.Thread(target=process_message)
        thread.daemon = True
        thread.start()
        
    except Exception as e:
        logger.error(f"❌ Error in handle_user_message for {session_id}: {str(e)}")
        import traceback
        traceback.print_exc()
        
        emit('bot_message', {
            "message": "❌ Sorry, I encountered an error. Please try again.",
            "timestamp": datetime.now().isoformat(),
            "type": "error"
        })
        logger.info(f"Main error message sent to {session_id}")
```

### **3. Enhanced CORS Configuration**
```python
# Initialize SocketIO with Teams-compatible CORS
socketio = SocketIO(app, cors_allowed_origins=[
    "https://teams.microsoft.com",
    "https://*.teams.microsoft.com",
    "https://teams.live.com",
    "https://*.teams.live.com",
    "https://indici-reports-assistant.onrender.com",
    "http://localhost:*",
    "http://127.0.0.1:*",
    "http://0.0.0.0:*",
    "*"  # Allow all origins for local development
], async_mode='threading', logger=True, engineio_logger=True)
```

## 🚀 **How to Debug Your Local Issue**

### **Step 1: Start Server with Debugging**
1. **Open terminal** in your project directory
2. **Run**: `python web/app.py`
3. **Wait for**: Server startup messages
4. **Look for**: "Running on http://127.0.0.1:10000"

### **Step 2: Test Browser Connection**
1. **Open browser**: `http://localhost:10000`
2. **Open browser console** (F12 → Console tab)
3. **Look for connection logs** in browser console
4. **Check server terminal** for connection logs

### **Step 3: Test Message Sending**
1. **Type message**: "hi" in the input field
2. **Click send button**
3. **Watch both**:
   - **Browser console** for client-side logs
   - **Server terminal** for server-side logs

## 🔍 **What to Look For**

### **In Server Terminal (Expected)**:
```
✅ Client connected: abc123 from 127.0.0.1
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)...
Welcome message sent to abc123
📨 Received message from abc123: 'hi'
Session info: {'connected_at': '2025-08-04...', 'message_count': 1}
🔄 Typing indicator sent to abc123
🔄 Starting async message processing for abc123
🤖 Calling chat_handler.handle_message...
✅ Chat handler response: {'response': '...', 'success': True}
📤 Sending response to abc123
✅ Response sent successfully to abc123
```

### **In Browser Console (Expected)**:
```
Initializing socket connection...
✅ Connected to server successfully
Global sendMessage called, chatApp exists: true
SendMessage called: {message: "hi", isConnected: true, socket: true}
Sending message to server: hi
```

### **Error Indicators to Watch For**:

#### **Server Terminal Errors**:
- ❌ `Error in handle_connect`
- ❌ `Error processing message`
- ❌ `Error in handle_user_message`
- ❌ `Connection error`

#### **Browser Console Errors**:
- ❌ `Not connected to server`
- ❌ `ChatApp not initialized`
- ❌ `Socket connection failed`
- ❌ `CORS error`

## 🛠 **Troubleshooting Steps**

### **If Server Won't Start**:
1. **Check port**: Make sure port 10000 is free
2. **Check Python**: Ensure virtual environment is activated
3. **Check dependencies**: Run `pip install -r requirements.txt`
4. **Check config**: Verify config.json and .env files exist

### **If Browser Won't Connect**:
1. **Clear cache**: Hard refresh (Ctrl+F5)
2. **Try incognito**: Test in private browsing mode
3. **Check firewall**: Ensure Windows firewall allows connection
4. **Try different browser**: Test Chrome, Firefox, Edge

### **If Messages Don't Send**:
1. **Check console**: Look for JavaScript errors
2. **Check network**: Verify Socket.IO requests in Network tab
3. **Check server logs**: Look for message processing errors
4. **Test manually**: Try `window.chatApp.sendMessage()` in console

## 📝 **Debug Commands**

### **Test Server Accessibility**:
```bash
# Test if server is running
curl http://localhost:10000
# Should return HTML page
```

### **Test Socket Connection**:
```javascript
// In browser console
console.log('Socket exists:', !!window.chatApp.socket);
console.log('Is connected:', window.chatApp.isConnected);
console.log('ChatApp exists:', !!window.chatApp);
```

### **Manual Message Test**:
```javascript
// In browser console
window.chatApp.socket.emit('user_message', { message: 'test' });
```

## 🎯 **Next Steps**

1. **Start the server** with the enhanced debugging
2. **Open browser** at `http://localhost:10000`
3. **Open browser console** (F12)
4. **Try sending "hi"**
5. **Share the output** from both:
   - **Server terminal logs**
   - **Browser console logs**

## 🔧 **Quick Fixes to Try**

### **Fix 1: Port Issue**
```bash
# Try different port
python -c "from web.app import app, socketio; socketio.run(app, host='0.0.0.0', port=8080, debug=True)"
```

### **Fix 2: Simple HTTP Test**
```bash
# Test basic HTTP (not Socket.IO)
python -c "from flask import Flask; app = Flask(__name__); app.run(host='0.0.0.0', port=9000)"
```

### **Fix 3: Network Interface**
```bash
# Try localhost only
python -c "from web.app import app, socketio; socketio.run(app, host='127.0.0.1', port=10000, debug=True)"
```

## 🎉 **Expected Result**

With the enhanced debugging, we'll be able to see exactly:
- ✅ **Where the connection fails** (if it does)
- ✅ **What errors occur** during message processing
- ✅ **Which component** is causing the issue
- ✅ **How to fix** the specific problem

**The comprehensive debugging will reveal exactly what's wrong with your localhost setup! 🔍**

Please start the server and try sending a message, then share both the server terminal output and browser console output so I can identify the exact issue.

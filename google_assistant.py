# google_assistant.py
import os
import json
import uuid
import logging
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.auth.transport.grpc import secure_authorized_channel

# Try to import the Assistant protobuf files
try:
    # Try the google-assistant-grpc package first
    import google.assistant.embedded.v1alpha2.embedded_assistant_pb2 as embedded_assistant_pb2
    import google.assistant.embedded.v1alpha2.embedded_assistant_pb2_grpc as embedded_assistant_pb2_grpc
    ASSISTANT_SDK_AVAILABLE = True
    print("✅ Google Assistant gRPC SDK available")
except ImportError:
    try:
        # Try alternative import paths
        from google.assistant.embedded.v1alpha2 import embedded_assistant_pb2, embedded_assistant_pb2_grpc
        ASSISTANT_SDK_AVAILABLE = True
        print("✅ Google Assistant SDK available (alternative path)")
    except ImportError:
        # Fallback: Use Google Cast API for direct device control
        try:
            import pychromecast
            ASSISTANT_SDK_AVAILABLE = "CAST"
            print("✅ Using Google Cast API for direct device control")
        except ImportError:
            try:
                import requests
                ASSISTANT_SDK_AVAILABLE = "REST"
                print("⚠️ Using REST API fallback for Google Assistant (protobuf not available)")
            except ImportError:
                ASSISTANT_SDK_AVAILABLE = False
                print("⚠️ Google Assistant SDK protobuf files not available. Assistant commands will be simulated.")

# Google Assistant SDK scopes
ASSISTANT_SCOPES = ['https://www.googleapis.com/auth/assistant-sdk-prototype']

# Assistant API configuration
ASSISTANT_API_ENDPOINT = 'embeddedassistant.googleapis.com'
DEFAULT_GRPC_DEADLINE = 60 * 3 + 5

# Device configuration - you may need to customize these
DEVICE_MODEL_ID = 'jarvis-assistant-device'  # You'll create this in Google Cloud Console
DEVICE_INSTANCE_ID = str(uuid.uuid4())
LANGUAGE_CODE = 'en-US'

def get_assistant_creds(creds_file="client_secret.json", token_file="assistant_token.json"):
    """
    Get credentials for Google Assistant SDK.
    """
    creds = None
    
    # 1) Load existing token if available
    if os.path.exists(token_file):
        try:
            creds = Credentials.from_authorized_user_file(token_file, ASSISTANT_SCOPES)
        except Exception as e:
            print(f"⚠️ Error loading existing Assistant credentials: {e}")
    
    # 2) If no valid creds, run through the OAuth2 flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                print("✅ Refreshed Assistant credentials")
            except Exception as e:
                print(f"⚠️ Failed to refresh credentials: {e}")
                creds = None
        
        if not creds:
            try:
                flow = InstalledAppFlow.from_client_secrets_file(creds_file, ASSISTANT_SCOPES)
                creds = flow.run_local_server(port=0)
                print("✅ Obtained new Assistant credentials")
            except Exception as e:
                print(f"❌ Failed to get Assistant credentials: {e}")
                return None
        
        # 3) Save the credentials for next time
        try:
            with open(token_file, "w", encoding="utf-8") as token:
                token.write(creds.to_json())
            print(f"💾 Saved Assistant credentials to {token_file}")
        except Exception as e:
            print(f"⚠️ Failed to save credentials: {e}")
    
    return creds

def test_assistant_connection():
    """
    Test the Assistant SDK connection.
    """
    try:
        creds = get_assistant_creds()
        if not creds:
            return "❌ Failed to get Assistant credentials"
        
        print("✅ Assistant credentials obtained successfully")
        print(f"   Valid: {creds.valid}")
        print(f"   Has refresh token: {bool(creds.refresh_token)}")
        
        return "✅ Google Assistant SDK credentials are ready"
        
    except Exception as e:
        return f"❌ Assistant connection test failed: {str(e)}"

def send_assistant_command_cast(command_text):
    """
    Send a command using Google Cast API to directly control devices.
    """
    try:
        from google_cast import cast_manager, parse_music_command
        
        # Parse the command to see if it's a music command
        music_info = parse_music_command(command_text)
        
        if music_info:
            query = music_info["query"]
            service = music_info["service"]
            
            if service == "spotify":
                result = cast_manager.play_spotify(query)
            elif service == "youtube":
                result = cast_manager.play_youtube(query)
            else:
                result = cast_manager.play_spotify(query)  # Default to Spotify
            
            return result
        else:
            # For non-music commands, try to send as voice command
            result = cast_manager.send_voice_command(command_text)
            return result
            
    except ImportError:
        return {
            "success": False,
            "message": "❌ Google Cast integration not available. Install pychromecast."
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"❌ Cast command failed: {str(e)}"
        }

def send_assistant_command_rest(command_text, creds):
    """
    Send a command using REST API approach (fallback when gRPC is not available).
    This requires a device model to be set up in Google Cloud Console.
    """
    import requests
    
    # This is a simplified approach - in reality, you'd need to:
    # 1. Set up a device model in Google Cloud Console
    # 2. Use the Google Assistant Service API
    # 3. Handle device registration properly
    
    return {
        "success": False,
        "message": "❌ REST API method requires device model setup. Use the setup instructions below.",
        "setup_instructions": get_setup_instructions()
    }

def get_setup_instructions():
    """
    Return detailed setup instructions for connecting to Google Home devices.
    """
    return """
🏠 To control your Google Home devices with Jarvis:

OPTION 1 (RECOMMENDED): Google Cast API - Direct Control
✅ Already set up! Your Jarvis can now discover and control Google Home devices directly.
- Automatically discovers devices on your network
- Can control volume, pause/play
- Can send voice commands to your Google Home

OPTION 2: Google Assistant SDK - Full Integration  
1. Go to Google Cloud Console (console.cloud.google.com)
2. Create or select a project
3. Enable the Google Assistant API
4. Go to the Google Assistant Console (console.actions.google.com)
5. Create a new project (link it to your Cloud project)
6. Set up device registration:
   - Go to Device Registration
   - Create a new device model
   - Device type: Speaker, Smart Display, etc.
   - Device model ID: jarvis-assistant-device
   - Download the credentials JSON

🎵 Available Commands:
- "play [song/artist] on Spotify"
- "play [video] on YouTube" 
- "set volume to [0-100]"
- "pause" / "resume"
- "what's playing?"
"""

def send_assistant_command(command_text):
    """
    Send a text command to Google Assistant using the gRPC API.
    This will actually communicate with your Google Home devices.
    """
    try:
        creds = get_assistant_creds()
        if not creds:
            return {
                "success": False,
                "message": "Failed to get Assistant credentials"
            }
        
        # Check if the Assistant SDK is available
        if ASSISTANT_SDK_AVAILABLE == "CAST":
            # Use Google Cast API for direct device control
            return send_assistant_command_cast(command_text)
        elif ASSISTANT_SDK_AVAILABLE == "REST":
            # Use REST API approach (requires device model setup)
            return send_assistant_command_rest(command_text, creds)
        elif not ASSISTANT_SDK_AVAILABLE:
            return {
                "success": True,
                "message": f"🎵 Simulated: Sent '{command_text}' to Google Assistant. (Full SDK integration requires additional setup)",
                "simulated": True,
                "note": "To control your Google Home devices, you need to set up a device model in Google Cloud Console."
            }
        
        # Try to use the gRPC API to send the command
        try:
            # Create a secure channel to the Assistant API
            channel = secure_authorized_channel(creds, Request(), ASSISTANT_API_ENDPOINT)
            assistant = embedded_assistant_pb2_grpc.EmbeddedAssistantStub(channel)
            
            # Create the text query request
            config = embedded_assistant_pb2.AssistConfig(
                audio_out_config=embedded_assistant_pb2.AudioOutConfig(
                    encoding='LINEAR16',
                    sample_rate_hertz=16000,
                    volume_percentage=50,
                ),
                dialog_state_in=embedded_assistant_pb2.DialogStateIn(
                    language_code=LANGUAGE_CODE,
                    conversation_state=b'',  # Empty for new conversation
                ),
                device_config=embedded_assistant_pb2.DeviceConfig(
                    device_id=DEVICE_INSTANCE_ID,
                    device_model_id=DEVICE_MODEL_ID,
                ),
                text_query=command_text,
            )
            
            # Send the request
            req = embedded_assistant_pb2.AssistRequest(config=config)
            responses = assistant.Assist([req], DEFAULT_GRPC_DEADLINE)
            
            # Process responses
            response_text = ""
            for response in responses:
                if response.dialog_state_out:
                    # Command was processed successfully
                    if response.dialog_state_out.supplemental_display_text:
                        response_text = response.dialog_state_out.supplemental_display_text
                
                if response.device_action:
                    # Device action was triggered (e.g., playing music)
                    return {
                        "success": True,
                        "message": f"✅ Successfully sent '{command_text}' to Google Assistant",
                        "response": response_text or "Command executed",
                        "device_action": True
                    }
            
            return {
                "success": True,
                "message": f"✅ Successfully sent '{command_text}' to Google Assistant",
                "response": response_text or "Command sent successfully"
            }
            
        except Exception as grpc_error:
            # If gRPC fails, provide helpful error message
            error_msg = str(grpc_error)
            
            if "device_model_id" in error_msg.lower():
                return {
                    "success": False,
                    "message": f"❌ Device model not set up. You need to create a device model in Google Cloud Console with ID: {DEVICE_MODEL_ID}",
                    "setup_needed": True
                }
            elif "permission" in error_msg.lower():
                return {
                    "success": False,
                    "message": "❌ Permission denied. Make sure your Google account has access to the Assistant SDK.",
                    "permission_error": True
                }
            else:
                return {
                    "success": False,
                    "message": f"❌ Assistant API error: {error_msg}",
                    "api_error": True
                }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"❌ Assistant command failed: {str(e)}"
        }

if __name__ == "__main__":
    # Test the Assistant connection
    result = test_assistant_connection()
    print(result)

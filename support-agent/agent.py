from dotenv import load_dotenv

from livekit import agents
from livekit.agents import (
    AgentServer,
    AgentSession,
    Agent,
    inference,
    room_io,
)
from livekit.plugins import groq, noise_cancellation , bey
from prompts import AGENT_INSTRUCTIONS
import os
from tools import send_email
from livekit.agents import BackgroundAudioPlayer, AudioConfig, BuiltinAudioClip


load_dotenv(".env.local")


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions=AGENT_INSTRUCTIONS,
            tools=[send_email]
        )


server = AgentServer()


@server.rtc_session(agent_name="my-agent")
async def my_agent(ctx: agents.JobContext):

    session = AgentSession(
        stt=groq.STT(
            model="whisper-large-v3-turbo",
            language="en",
        ),

        llm=groq.LLM(
            model="openai/gpt-oss-120b"
        ),

        tts=inference.TTS(
            model="rime/coda",
            voice="celeste",
            language="en",
        ),
    )
    avatar = bey.AvatarSession(
        avatar_id=os.environ.get("BEY_AVATAR_ID"),
    )
    await avatar.start(session,room=ctx.room)
    await session.start(
        room=ctx.room,
        agent=Assistant(),
        room_options=room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(
                noise_cancellation=noise_cancellation.BVC(),
                video_enabled=True,
            ),
        ),
    )
    background_audio=BackgroundAudioPlayer(
        thinking_sound=[
            AudioConfig(BuiltinAudioClip.KEYBOARD_TYPING,volume=1),
            AudioConfig(BuiltinAudioClip.KEYBOARD_TYPING2,volume=1),
        ],
    )
    await background_audio.start(room=ctx.room,agent_session=session)
    await session.generate_reply(
        instructions="Greet the user and offer your assistance."
    )


if __name__ == "__main__":
    agents.cli.run_app(server)
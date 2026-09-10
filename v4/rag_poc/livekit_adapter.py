from __future__ import annotations

import asyncio
import uuid
from dataclasses import asdict

from .timing import span

from livekit import rtc
from livekit.agents import Agent, AgentSession, llm, stt
from livekit.agents.types import DEFAULT_API_CONNECT_OPTIONS
from livekit.agents.voice import io


class ReplaySTT(stt.STT):
    """Input provider contract fixture; received audio is NOT recognized."""
    def __init__(self):
        super().__init__(capabilities=stt.STTCapabilities(streaming=True, interim_results=True,
                                                        offline_recognize=False))
        self.frames = 0
        self.frame_received = asyncio.Event()
        self.events = asyncio.Queue()
        self.streams = []

    async def _recognize_impl(self, buffer, **kwargs):
        raise NotImplementedError("Scripted streaming STT only")

    def stream(self, *, conn_options=DEFAULT_API_CONNECT_OPTIONS, **kwargs):
        stream = ReplayStream(stt=self, conn_options=conn_options)
        self.streams.append(stream)
        return stream

    async def close(self):
        for stream in self.streams:
            await stream.aclose()


class ReplayStream(stt.RecognizeStream):
    async def _run(self):
        provider = self._stt

        async def audio():
            async for frame in self._input_ch:
                if isinstance(frame, rtc.AudioFrame):
                    provider.frames += 1
                    provider.frame_received.set()

        task = asyncio.create_task(audio())
        try:
            await provider.frame_received.wait()
            while True:
                self._event_ch.send_nowait(await provider.events.get())
        finally:
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)


class Silence(io.AudioInput):
    def __init__(self):
        super().__init__(label="v4-scripted-audio")
        self.sent = False
        self.closed = asyncio.Event()

    async def __anext__(self):
        if not self.sent:
            self.sent = True
            return rtc.AudioFrame(data=bytes(640), sample_rate=16000,
                                  num_channels=1, samples_per_channel=320)
        await self.closed.wait()
        raise StopAsyncIteration


class PipelineLLM(llm.LLM):
    """Real SDK LLM provider node; endpoint/tool loop belongs to Pipeline."""
    def __init__(self, pipeline, bundles):
        super().__init__()
        self.pipeline, self.bundles = pipeline, bundles

    def chat(self, *, chat_ctx, tools=None, conn_options=DEFAULT_API_CONNECT_OPTIONS, **kwargs):
        return PipelineStream(self, chat_ctx=chat_ctx, tools=tools or [], conn_options=conn_options)


class PipelineStream(llm.LLMStream):
    async def _run(self):
        markers = [m.text_content for m in self.chat_ctx.items if isinstance(m, llm.ChatMessage)
                   and m.role == "assistant" and (m.text_content or "").startswith("RAG_BUNDLE:")]
        key = markers[-1].partition(":")[2] if markers else None
        bundle = self._llm.bundles.get(key)
        if bundle is None:
            raise RuntimeError("missing current-turn retrieval bundle")
        answer = await self._llm.pipeline.answer(bundle)
        self._event_ch.send_nowait(llm.ChatChunk(id=str(bundle.turn),
            delta=llm.ChoiceDelta(role="assistant", content=answer)))


class PipelineAgent(Agent):
    def __init__(self, pipeline):
        super().__init__(instructions="Answer only from this turn's retrieved sample catalog data.")
        self.pipeline = pipeline
        self.bundles = {}
        self.results = []
        self.confirmed = []
        self.segments = []
        self.interim = ""
        self.input_open = False
        self.processed = asyncio.Queue()

    async def stt_node(self, audio, model_settings):
        async for event in Agent.default.stt_node(self, audio, model_settings):
            if event.type == stt.SpeechEventType.START_OF_SPEECH and not self.input_open:
                self.pipeline.start_turn(self.confirmed)
                self.segments, self.interim = [], ""
                self.input_open = True
            elif self.input_open and event.alternatives:
                text = event.alternatives[0].text
                if event.type == stt.SpeechEventType.FINAL_TRANSCRIPT:
                    self.segments.append(text)
                    self.interim = ""
                elif event.type == stt.SpeechEventType.INTERIM_TRANSCRIPT:
                    self.interim = text
                if event.type in (stt.SpeechEventType.FINAL_TRANSCRIPT, stt.SpeechEventType.INTERIM_TRANSCRIPT):
                    self.pipeline.observe(" ".join([*self.segments, self.interim]).strip())
            yield event
            self.processed.put_nowait(event.type)

    async def on_user_turn_completed(self, turn_ctx, new_message):
        bundle = await self.pipeline.finish(new_message.text_content or "")
        self.input_open = False
        self.bundles.clear()
        key = uuid.uuid4().hex
        self.bundles[key] = bundle
        self.results.append(bundle)
        turn_ctx.add_message(role="assistant", content="RAG_BUNDLE:" + key)


async def replay_session(pipeline, turns):
    """Run ordered {partials:[str], final:str, gap_ms:number} turns through SDK EOT."""
    agent = PipelineAgent(pipeline)
    provider, audio = ReplaySTT(), Silence()
    model = PipelineLLM(pipeline, agent.bundles)
    session = AgentSession(llm=model, stt=provider, vad=None, tts=None,
        turn_handling={"turn_detection": "stt", "endpointing": {"min_delay": 0.0},
                       "preemptive_generation": {"enabled": False}}, user_away_timeout=None)
    session.input.audio = audio
    replies = asyncio.Queue()

    def item_added(event):
        if isinstance(event.item, llm.ChatMessage) and event.item.role == "assistant":
            replies.put_nowait(event.item.text_content)

    session.on("conversation_item_added", item_added)

    async def send(kind, text=""):
        with span("stt_event_dispatch", sink=pipeline.timings, turn=pipeline.turn + (kind == stt.SpeechEventType.START_OF_SPEECH), stt_event=kind.value):
            provider.events.put_nowait(stt.SpeechEvent(type=kind, alternatives=
                [stt.SpeechData(language="en", text=text)] if text else []))
            assert await asyncio.wait_for(agent.processed.get(), 3) == kind

    try:
        await session.start(agent=agent, record=False)
        await asyncio.wait_for(provider.frame_received.wait(), 3)
        for turn in turns:
            await send(stt.SpeechEventType.START_OF_SPEECH)
            for text in turn.get("partials", []):
                await send(stt.SpeechEventType.INTERIM_TRANSCRIPT, text)
                await asyncio.sleep(max(0, turn.get("gap_ms", 150)) / 1000)
            with span("final_to_full_answer", sink=pipeline.timings, turn=pipeline.turn):
                await send(stt.SpeechEventType.FINAL_TRANSCRIPT, turn["final"])
                await send(stt.SpeechEventType.END_OF_SPEECH)
                answer = await asyncio.wait_for(replies.get(), pipeline.final_timeout + pipeline.answer_timeout + 5)
            agent.confirmed.extend([{"role": "user", "content": turn["final"]},
                                    {"role": "assistant", "content": answer}])
        return {"turns": [asdict(b) for b in agent.results], "trace": pipeline.trace,
                "stt_streams": len(provider.streams), "audio_frames": provider.frames,
                "history": [{"role": m.role, "text": m.text_content} for m in session.history.items
                            if isinstance(m, llm.ChatMessage)]}
    finally:
        session.off("conversation_item_added", item_added)
        await session.aclose()
        audio.closed.set()
        await provider.close()
        if await pipeline.close():
            raise RuntimeError("pipeline cleanup exceeded its bound")

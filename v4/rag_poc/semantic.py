"""Independent dense-embedding cosine arm. No lexical/hash similarity fallback."""
import asyncio
import math
from pathlib import Path
import time

from .models import Query, ContractError
from .timing import span

MODEL = 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'
REPO = 'qdrant/paraphrase-multilingual-MiniLM-L12-v2-onnx-Q'
REVISION = 'faf4aa4225822f3bc6376869cb1164e8e3feedd0'


def query_text(query):
    q = Query.parse(query.json())
    # Same structured fields available to exact comparator; no user text/history
    # duplicated on both sides, and no hand-coded entity/number acceptance guard.
    fields = [f'{name}: {value}' for name, value in q.json().items() if value is not None]
    return 'Retrieve catalog products. ' + '; '.join(fields)


def cosine(a, b):
    if len(a) != len(b) or not a or not all(math.isfinite(float(x)) for x in [*a, *b]):
        raise ContractError('invalid embedding dimensions or nonfinite values')
    na, nb = math.sqrt(sum(float(x)**2 for x in a)), math.sqrt(sum(float(x)**2 for x in b))
    if na == 0 or nb == 0:
        raise ContractError('zero embedding norm')
    return max(-1.0, min(1.0, sum(float(x)*float(y) for x,y in zip(a,b))/(na*nb)))


class LocalEmbeddings:
    def __init__(self, model):
        self.model = model
        self.pending = None

    @classmethod
    def load(cls, cache_dir):
        from huggingface_hub import snapshot_download
        from fastembed import TextEmbedding
        with span('embedding_model_load', model=MODEL, revision=REVISION):
            path = snapshot_download(REPO, revision=REVISION, token=False,
                cache_dir=str(cache_dir), allow_patterns=['*.json', 'model_optimized.onnx'])
            model = TextEmbedding(model_name=MODEL, specific_model_path=path, threads=2,
                                  providers=['CPUExecutionProvider'])
        return cls(model)

    async def encode(self, texts):
        # One native inference batch at a time; cancelled Python await does not
        # pretend that the underlying ONNX worker stopped. Busy fails to demand.
        if self.pending is not None and not self.pending.done():
            raise RuntimeError('embedding worker busy')
        with span('embedding_inference', model=MODEL, texts=len(texts)):
            self.pending = asyncio.create_task(asyncio.to_thread(
                lambda: [v.tolist() for v in self.model.embed(texts)]))
            self.pending.add_done_callback(lambda t: t.exception() if not t.cancelled() else None)
            result = await asyncio.shield(self.pending)
            if len(result) != len(texts) or any(len(v) != 384 for v in result):
                raise ContractError('unexpected model output dimensions')
            return result

    async def close(self):
        if self.pending is not None:
            await asyncio.shield(self.pending)


class SemanticChecker:
    def __init__(self, embeddings, *, threshold):
        if not math.isfinite(threshold) or not -1 <= threshold <= 1:
            raise ValueError('semantic threshold must be finite and within [-1, 1]')
        self.embeddings, self.threshold = embeddings, threshold
        self.metrics = []

    async def select(self, final_text, context, final_query, candidates):
        # Builder already resolved final Query; no hidden LLM/exact fallback.
        started = time.perf_counter()
        record = {'model': MODEL, 'revision': REVISION, 'dimension': 384,
                  'threshold': self.threshold, 'scores': [], 'selected_candidate': None,
                  'status': 'error', 'cache': 'none'}
        self.metrics.append(record)
        try:
            if candidates:
                texts = [query_text(final_query)] + [query_text(Query.parse(c['query'])) for c in candidates]
                vectors = await self.embeddings.encode(texts)
                with span('cosine_comparison', threshold=self.threshold) as log:
                    for candidate, vector in zip(candidates, vectors[1:]):
                        score = cosine(vectors[0], vector)
                        record['scores'].append({'candidate_id': candidate['id'], 'cosine': score,
                            'accepted': score >= self.threshold, 'completed': candidate['completed']})
                    eligible = [s for s in record['scores'] if s['accepted']]
                    eligible.sort(key=lambda s: (not s['completed'], -s['cosine'], s['candidate_id']))
                    if eligible:
                        record['selected_candidate'] = eligible[0]['candidate_id']
                    log.update(scores=record['scores'], selected_candidate=record['selected_candidate'])
            record['status'] = 'ok'
            return record['selected_candidate']
        except asyncio.CancelledError:
            record['status'] = 'cancelled'
            raise
        except Exception as exc:
            record['error_type'] = type(exc).__name__
            raise
        finally:
            record['time_spent_ms'] = (time.perf_counter()-started)*1000

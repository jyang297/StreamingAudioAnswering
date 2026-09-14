"""Reuse v5 turn ownership, scheduling and independent final-query policy."""
from .compat import BasePipeline, SQLPipeline


class MultiTablePipeline(SQLPipeline):
    async def answer_loop(self, bundle):
        if bundle.path == "no_query":
            return "Please clarify the entity, relationship or conditions to query."
        if not bundle.evidence or bundle.path in {"final_error", "final_timeout"}:
            return "I could not obtain verified database evidence for this request."
        return await BasePipeline.answer_loop(self, bundle)

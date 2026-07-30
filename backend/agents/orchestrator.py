import logging
import uuid
from datetime import datetime, timezone
from typing import Callable, Awaitable

from agents.base import AgentContext, AgentStatus
from agents.topic_decomposer import TopicDecomposer
from agents.debater import Debater
from agents.judge import Judge
from agents.bias_detector import BiasDetector
from agents.devils_advocate import DevilsAdvocate
from agents.critic import Critic
from agents.fact_checker import FactChecker
from agents.memory_agent import MemoryAgent
from agents.summariser import Summariser
from agents.audience_agent import AudienceAgent
from agents.meta_evaluator import MetaEvaluator
from core.checkpoint import save_checkpoint, load_checkpoint
from db.supabase_client import supabase_service

logger = logging.getLogger(__name__)

# Dynamic round logic constants
MIN_ROUNDS = 2
MAX_ROUNDS = 5
CONVERGENCE_THRESHOLD = 0.5      # Score gap below this = convergence
CONVERGENCE_CONSECUTIVE = 2      # Consecutive rounds needed to trigger
DOMINANCE_THRESHOLD = 2.0        # Score gap above this = dominance
DOMINANCE_CONSECUTIVE = 3        # Consecutive rounds needed to trigger
DEVILS_ADVOCATE_GAP = 2.0        # Gap above this triggers Devil's Advocate
DEVILS_ADVOCATE_CONSECUTIVE = 2  # Consecutive rounds needed to trigger
CRITIC_INTERVAL = 3              # Critic fires every N rounds


class Orchestrator:
    def __init__(self, emit: Callable[[str, dict], Awaitable[None]]):
        """
        emit: async function that sends a WebSocket event to the frontend.
        Called as: await emit("event_type", {...data...})
        """
        self.emit = emit

        # Instantiate all agents
        self.topic_decomposer = TopicDecomposer()
        self.debater_a = Debater("A")
        self.debater_b = Debater("B")
        self.judge = Judge()
        self.bias_detector = BiasDetector()
        self.devils_advocate = DevilsAdvocate()
        self.critic = Critic()
        self.fact_checker = FactChecker()
        self.memory_agent = MemoryAgent()
        self.summariser = Summariser()
        self.audience_agent = AudienceAgent()
        self.meta_evaluator = MetaEvaluator()

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    async def run_debate(
        self,
        debate_id: str,
        user_id: str,
        topic: str,
        audience_persona: str = "general public",
    ) -> dict:
        """Run a full debate and return the final result dict."""

        await self.emit("debate_started", {"debate_id": debate_id, "topic": topic})

        # Try to resume from checkpoint
        checkpoint = await load_checkpoint(debate_id)
        if checkpoint:
            logger.info(f"[Orchestrator] Resuming debate {debate_id} from checkpoint")
            await self.emit("debate_resumed", {"debate_id": debate_id})

        # --- Phase 1: Decompose topic ---
        await self.emit("agent_thinking", {"agent": "TopicDecomposer"})
        base_context = AgentContext(
            debate_id=debate_id, user_id=user_id, topic=topic,
            sub_topic=topic, round_number=0,
            stance_a="FOR", stance_b="AGAINST",
            audience_persona=audience_persona,
        )
        decomp_result = await self.topic_decomposer.run_with_retry(base_context)
        sub_topics = decomp_result.data or [{
            "id": 1, "title": topic, "question": topic,
            "suggested_stance_a": "FOR", "suggested_stance_b": "AGAINST",
        }]

        await self.emit("topic_decomposed", {"sub_topics": sub_topics})

        all_sub_results = []
        overall_score_a = 0.0
        overall_score_b = 0.0

        # --- Phase 2: Run each sub-debate ---
        for sub_index, sub in enumerate(sub_topics):
            sub_result = await self._run_sub_debate(
                debate_id=debate_id,
                user_id=user_id,
                topic=topic,
                sub=sub,
                sub_index=sub_index,
                total_subs=len(sub_topics),
                audience_persona=audience_persona,
            )
            all_sub_results.append(sub_result)
            overall_score_a += sub_result.get("final_score_a", 0)
            overall_score_b += sub_result.get("final_score_b", 0)

        # --- Phase 3: Meta evaluation ---
        await self.emit("agent_thinking", {"agent": "MetaEvaluator"})
        meta_context = AgentContext(
            debate_id=debate_id, user_id=user_id, topic=topic,
            sub_topic=topic, round_number=0,
            stance_a="FOR", stance_b="AGAINST",
            score_history=[{
                "total_a": overall_score_a / len(sub_topics),
                "total_b": overall_score_b / len(sub_topics),
                "winner": "debater_a" if overall_score_a > overall_score_b else "debater_b",
            }],
        )
        meta_result = await self.meta_evaluator.run_with_retry(meta_context)
        meta_data = meta_result.data or {}

        # --- Determine overall winner ---
        if overall_score_a > overall_score_b:
            winner = "debater_a"
        elif overall_score_b > overall_score_a:
            winner = "debater_b"
        else:
            winner = "tie"

        quality_score = meta_data.get("quality_score", 7.0)

        # --- Save to Supabase ---
        await self._save_debate_record(
            debate_id=debate_id, user_id=user_id, topic=topic,
            winner=winner, quality_score=quality_score,
            total_rounds=sum(s.get("rounds_run", 0) for s in all_sub_results),
        )

        final_result = {
            "debate_id": debate_id,
            "topic": topic,
            "winner": winner,
            "overall_score_a": round(overall_score_a / len(sub_topics), 2),
            "overall_score_b": round(overall_score_b / len(sub_topics), 2),
            "quality_score": quality_score,
            "total_rounds": sum(s.get("rounds_run", 0) for s in all_sub_results),
            "meta_evaluation": meta_data.get("evaluation", ""),
            "sub_debates": all_sub_results,
        }

        await self.emit("debate_complete", final_result)
        return final_result

    # ------------------------------------------------------------------
    # Sub-debate runner
    # ------------------------------------------------------------------

    async def _run_sub_debate(
        self, debate_id, user_id, topic, sub, sub_index, total_subs, audience_persona
    ) -> dict:
        sub_topic = sub.get("question", sub.get("title", topic))
        stance_a = sub.get("suggested_stance_a", "FOR")
        stance_b = sub.get("suggested_stance_b", "AGAINST")

        await self.emit("sub_debate_started", {
            "sub_index": sub_index + 1,
            "total_subs": total_subs,
            "sub_topic": sub_topic,
            "stance_a": stance_a,
            "stance_b": stance_b,
        })

        score_history = []
        round_results = []
        rubric = None
        consecutive_convergence = 0
        consecutive_dominance = 0
        consecutive_da_trigger = 0

        for round_num in range(1, MAX_ROUNDS + 1):
            round_data = await self._run_round(
                debate_id=debate_id, user_id=user_id, topic=topic,
                sub_topic=sub_topic, round_num=round_num,
                stance_a=stance_a, stance_b=stance_b,
                score_history=score_history, rubric=rubric,
                audience_persona=audience_persona,
            )
            round_results.append(round_data)
            score_history.append(round_data["scores"])

            # Update rubric if critic fired
            if round_data.get("new_rubric"):
                rubric = round_data["new_rubric"]

            # Save checkpoint after every round
            await save_checkpoint(
                debate_id=debate_id,
                sub_debate_id=str(uuid.uuid4()),
                round_number=round_num,
                state={
                    "sub_index": sub_index,
                    "round_num": round_num,
                    "score_history": score_history,
                },
            )

            # Skip exit checks until minimum rounds done
            if round_num < MIN_ROUNDS:
                continue

            total_a = round_data["scores"].get("total_a", 5)
            total_b = round_data["scores"].get("total_b", 5)
            gap = abs(total_a - total_b)

            # Convergence check
            if gap < CONVERGENCE_THRESHOLD:
                consecutive_convergence += 1
            else:
                consecutive_convergence = 0

            # Dominance check
            if gap >= DOMINANCE_THRESHOLD:
                consecutive_dominance += 1
            else:
                consecutive_dominance = 0

            # Devil's Advocate trigger check
            if gap >= DEVILS_ADVOCATE_GAP:
                consecutive_da_trigger += 1
            else:
                consecutive_da_trigger = 0

            if consecutive_convergence >= CONVERGENCE_CONSECUTIVE:
                await self.emit("debate_exit", {"reason": "convergence", "round": round_num})
                break

            if consecutive_dominance >= DOMINANCE_CONSECUTIVE:
                await self.emit("debate_exit", {"reason": "dominance", "round": round_num})
                break

            if round_data.get("is_repetitive"):
                await self.emit("debate_exit", {"reason": "repetition", "round": round_num})
                break

        # Tally final scores for this sub-debate
        final_a = sum(r["scores"].get("total_a", 0) for r in round_results) / len(round_results)
        final_b = sum(r["scores"].get("total_b", 0) for r in round_results) / len(round_results)
        sub_winner = "debater_a" if final_a > final_b else ("debater_b" if final_b > final_a else "tie")

        await self.emit("sub_debate_complete", {
            "sub_topic": sub_topic,
            "winner": sub_winner,
            "final_score_a": round(final_a, 2),
            "final_score_b": round(final_b, 2),
        })

        return {
            "sub_topic": sub_topic,
            "stance_a": stance_a,
            "stance_b": stance_b,
            "rounds_run": len(round_results),
            "winner": sub_winner,
            "final_score_a": round(final_a, 2),
            "final_score_b": round(final_b, 2),
            "rounds": round_results,
        }

    # ------------------------------------------------------------------
    # Single round runner
    # ------------------------------------------------------------------

    async def _run_round(
        self, debate_id, user_id, topic, sub_topic, round_num,
        stance_a, stance_b, score_history, rubric, audience_persona
    ) -> dict:
        await self.emit("round_started", {"round_number": round_num, "sub_topic": sub_topic})

        context = AgentContext(
            debate_id=debate_id, user_id=user_id, topic=topic,
            sub_topic=sub_topic, round_number=round_num,
            stance_a=stance_a, stance_b=stance_b,
            score_history=score_history, rubric=rubric,
            audience_persona=audience_persona,
        )

        # 1. Fact Checker
        await self.emit("agent_thinking", {"agent": "FactChecker"})
        fact_result = await self.fact_checker.run_with_retry(context)
        context.fact_context = (fact_result.data or {}).get("fact_context", "")

        # 2. Retrieve memory for each debater
        context.memory_context = await self.memory_agent.retrieve_history(debate_id, "A")

        # 3. Debater A
        await self.emit("agent_thinking", {"agent": "DebaterA"})
        result_a = await self.debater_a.run_with_retry(context)
        context.argument_a = (result_a.data or {}).get("argument", "")
        await self.emit("argument_made", {
            "debater": "A", "stance": stance_a,
            "argument": context.argument_a, "round": round_num,
        })

        # 4. Retrieve memory for B then Debater B
        context.memory_context = await self.memory_agent.retrieve_history(debate_id, "B")
        await self.emit("agent_thinking", {"agent": "DebaterB"})
        result_b = await self.debater_b.run_with_retry(context)
        context.argument_b = (result_b.data or {}).get("argument", "")
        await self.emit("argument_made", {
            "debater": "B", "stance": stance_b,
            "argument": context.argument_b, "round": round_num,
        })

        # 5. Bias Detector
        await self.emit("agent_thinking", {"agent": "BiasDetector"})
        bias_result = await self.bias_detector.run_with_retry(context)
        bias_data = bias_result.data or {}
        context.bias_flags = bias_data.get("flags_a", []) + bias_data.get("flags_b", [])
        if bias_data.get("any_flags"):
            await self.emit("bias_detected", {"flags": context.bias_flags})

        # 6. Judge
        await self.emit("agent_thinking", {"agent": "Judge"})
        judge_result = await self.judge.run_with_retry(context)
        judge_data = judge_result.data or {}
        await self.emit("round_scored", {
            "round": round_num,
            "total_a": judge_data.get("total_a"),
            "total_b": judge_data.get("total_b"),
            "winner": judge_data.get("winner"),
            "key_insight": judge_data.get("key_insight"),
        })

        # 7. Critic (every 3 rounds)
        new_rubric = None
        if round_num % CRITIC_INTERVAL == 0:
            await self.emit("agent_thinking", {"agent": "Critic"})
            critic_result = await self.critic.run_with_retry(context)
            if critic_result.status == AgentStatus.OK and critic_result.data:
                new_rubric = critic_result.data.get("updated_rubric")
                await self.emit("rubric_updated", {"changes": critic_result.data.get("changes_made", [])})

        # 8. Devil's Advocate (when gap threshold met for consecutive rounds)
        gap = abs(judge_data.get("total_a", 5) - judge_data.get("total_b", 5))
        if gap >= DEVILS_ADVOCATE_GAP and len(score_history) >= DEVILS_ADVOCATE_CONSECUTIVE - 1:
            await self.emit("agent_thinking", {"agent": "DevilsAdvocate"})
            da_context = AgentContext(
                debate_id=debate_id, user_id=user_id, topic=topic,
                sub_topic=sub_topic, round_number=round_num,
                stance_a=stance_a, stance_b=stance_b,
                argument_a=context.argument_a, argument_b=context.argument_b,
                score_history=score_history,
            )
            da_result = await self.devils_advocate.run_with_retry(da_context)
            da_data = da_result.data or {}
            if da_data.get("advice"):
                await self.emit("devils_advocate_fired", {
                    "for_debater": da_data.get("for_debater"),
                    "advice": da_data.get("advice"),
                })

        # 9. Memory Agent — store + novelty check
        await self.emit("agent_thinking", {"agent": "MemoryAgent"})
        memory_result = await self.memory_agent.run(context)
        memory_data = memory_result.data or {}
        is_repetitive = memory_data.get("is_repetitive", False)

        # 10. Summariser
        await self.emit("agent_thinking", {"agent": "Summariser"})
        summary_result = await self.summariser.run_with_retry(context)
        summary = (summary_result.data or {}).get("summary", "")
        await self.emit("round_summary", {"round": round_num, "summary": summary})

        # 11. Audience Agent
        await self.emit("agent_thinking", {"agent": "AudienceAgent"})
        audience_result = await self.audience_agent.run_with_retry(context)
        audience_data = audience_result.data or {}
        await self.emit("audience_reacted", {
            "persona": audience_data.get("persona"),
            "reaction": audience_data.get("reaction"),
        })

        return {
            "round": round_num,
            "argument_a": context.argument_a,
            "argument_b": context.argument_b,
            "bias_flags": context.bias_flags,
            "scores": {
                "total_a": judge_data.get("total_a", 0),
                "total_b": judge_data.get("total_b", 0),
                "winner": judge_data.get("winner", "tie"),
                "reasoning": judge_data.get("reasoning", {}),
                "key_insight": judge_data.get("key_insight", ""),
            },
            "summary": summary,
            "audience_reaction": audience_data.get("reaction", ""),
            "novelty_score": memory_data.get("novelty_score", 1.0),
            "is_repetitive": is_repetitive,
            "new_rubric": new_rubric,
        }

    # ------------------------------------------------------------------
    # Supabase record
    # ------------------------------------------------------------------

    async def _save_debate_record(
        self, debate_id, user_id, topic, winner, quality_score, total_rounds
    ):
        try:
            supabase_service.table("debates").update({
                "status": "completed",
                "completed_at": datetime.now(timezone.utc).isoformat(),
                "winner": winner,
                "quality_score": quality_score,
                "total_rounds": total_rounds,
            }).eq("debate_id", debate_id).execute()
            logger.info(f"[Orchestrator] Debate {debate_id} saved to Supabase.")
        except Exception as e:
            logger.error(f"[Orchestrator] Failed to save debate record: {e}")
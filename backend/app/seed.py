"""
Seeds demo HCPs and a realistic, *current* interaction history for each, so the
app is immediately demonstrable — search_interactions, hcp_insights, and the
history table all have real, recent data to work with instead of the agent
having to guess (which is what produces hallucinated dates).

Two things make this safe to run on every container start (the Dockerfile calls
`python -m app.seed` before uvicorn):

  * HCPs are get-or-created by name — never duplicated.
  * Interaction history is seeded per-HCP only if that HCP has none yet, so a
    fresh HCP gets backfilled without touching HCPs that already have data.

All interaction dates are RELATIVE to today (`date.today() - N days`), so the
demo data always reads as recent no matter when the container is started.
"""
import asyncio
from datetime import date, timedelta

from sqlalchemy import select

from app.db.database import AsyncSessionLocal, init_db
from app.db.models import HCP, Interaction

DEMO_HCPS = [
    dict(name="Dr. Anjali Mehta", specialty="Cardiology", institution="Kokilaben Hospital", city="Mumbai", tier="A",
         email="anjali.mehta@example-hospital.in", phone="+91 98200 00001"),
    dict(name="Dr. Rohan Sharma", specialty="Endocrinology", institution="Lilavati Hospital", city="Mumbai", tier="A",
         email="rohan.sharma@example-hospital.in", phone="+91 98200 00002"),
    dict(name="Dr. Priya Nair", specialty="Oncology", institution="Tata Memorial", city="Mumbai", tier="B",
         email="priya.nair@example-hospital.in", phone="+91 98200 00003"),
    dict(name="Dr. Vikram Desai", specialty="General Medicine", institution="Fortis Hospital", city="Bangalore", tier="C",
         email="vikram.desai@example-hospital.in", phone="+91 98200 00004"),
]


def _days_ago(n: int) -> date:
    return date.today() - timedelta(days=n)


# History templates keyed by HCP name. Dates are day-offsets from today.
def _history_for(name: str, hcp_id: str) -> list[Interaction]:
    common = dict(hcp_id=hcp_id, channel="structured")

    if name == "Dr. Anjali Mehta":
        return [
            Interaction(**common, interaction_type="visit", interaction_date=_days_ago(58), interaction_time="10:30",
                        attendees=["Clinic nurse"], products_discussed=["Cardivax"],
                        samples_dropped=["Cardivax 10mg"], materials_shared=["Cardivax efficacy deck"],
                        topics_discussed="Introductory visit; discussed Cardivax efficacy data.",
                        outcomes="Agreed to review the Phase III data before next visit.",
                        summary="First meeting with Dr. Mehta; introduced Cardivax and shared Phase III efficacy data.",
                        sentiment="neutral", follow_up_required=False),
            Interaction(**common, interaction_type="visit", interaction_date=_days_ago(23), interaction_time="15:00",
                        products_discussed=["Cardivax"], samples_dropped=["Cardivax 10mg", "Cardivax 20mg"],
                        materials_shared=[], topics_discussed="Follow-up visit; asked about elderly dosing safety.",
                        outcomes="Will consider broader prescribing pending elderly-dosing data.",
                        summary="Dr. Mehta requested elderly-patient dosing safety data for Cardivax.",
                        sentiment="positive", follow_up_required=True,
                        follow_up_notes="Send elderly dosing safety study PDF."),
        ]
    if name == "Dr. Rohan Sharma":
        return [
            Interaction(**common, interaction_type="visit", interaction_date=_days_ago(41), interaction_time="09:15",
                        products_discussed=["GlucoStead"], samples_dropped=["GlucoStead 500mg"],
                        materials_shared=["GlucoStead titration guide"],
                        topics_discussed="Reviewed GlucoStead titration for type-2 diabetes patients.",
                        outcomes="Started two patients on GlucoStead; will monitor HbA1c.",
                        summary="Dr. Sharma initiated GlucoStead for two type-2 diabetes patients.",
                        sentiment="positive", follow_up_required=True,
                        follow_up_notes="Check HbA1c results at next visit."),
            Interaction(**common, interaction_type="call", interaction_date=_days_ago(9), interaction_time="17:45",
                        products_discussed=["GlucoStead"], topics_discussed="Phone check-in on GlucoStead tolerability.",
                        outcomes="Good tolerability reported; considering expanding use.",
                        summary="Dr. Sharma reported good GlucoStead tolerability and may prescribe more widely.",
                        sentiment="positive", follow_up_required=False),
        ]
    if name == "Dr. Priya Nair":
        return [
            Interaction(**common, interaction_type="visit", interaction_date=_days_ago(35), interaction_time="11:00",
                        attendees=["Oncology fellow"], products_discussed=["OncoBoost"],
                        materials_shared=["OncoBoost Phase III summary"],
                        topics_discussed="Presented OncoBoost Phase III efficacy in adjuvant setting.",
                        outcomes="Interested; requested full Phase III PDF and sample availability.",
                        summary="Dr. Nair showed strong interest in OncoBoost after the Phase III presentation.",
                        sentiment="positive", follow_up_required=True,
                        follow_up_notes="Send OncoBoost Phase III PDF; confirm sample availability."),
            Interaction(**common, interaction_type="visit", interaction_date=_days_ago(12), interaction_time="14:30",
                        products_discussed=["OncoBoost"], samples_dropped=[],
                        topics_discussed="Discussed OncoBoost access pathway and upcoming sample drop.",
                        outcomes="Expects product samples at the next meeting.",
                        summary="Dr. Nair expects OncoBoost samples at the next visit; access pathway clarified.",
                        sentiment="positive", follow_up_required=True,
                        follow_up_notes="Bring OncoBoost samples to next meeting."),
        ]
    if name == "Dr. Vikram Desai":
        return [
            Interaction(**common, interaction_type="visit", interaction_date=_days_ago(20), interaction_time="12:15",
                        products_discussed=["Cardivax"], materials_shared=["Cardivax primary-care leaflet"],
                        topics_discussed="Introduced Cardivax for primary-care hypertension management.",
                        outcomes="Cautious; wants real-world evidence before prescribing.",
                        summary="Dr. Desai was cautious on Cardivax and asked for real-world evidence.",
                        sentiment="neutral", follow_up_required=True,
                        follow_up_notes="Share real-world evidence summary for Cardivax."),
        ]
    return []


async def seed():
    await init_db()
    async with AsyncSessionLocal() as db:
        # 1. Get-or-create the demo HCPs by name.
        existing = {h.name: h for h in (await db.execute(select(HCP))).scalars().all()}
        created = 0
        for data in DEMO_HCPS:
            if data["name"] not in existing:
                hcp = HCP(**data)
                db.add(hcp)
                existing[data["name"]] = hcp
                created += 1
        if created:
            await db.commit()
            for h in existing.values():
                await db.refresh(h)

        # 2. Backfill interaction history for any HCP that has none.
        added = 0
        for name, hcp in existing.items():
            has_history = (
                await db.execute(select(Interaction.id).where(Interaction.hcp_id == hcp.id).limit(1))
            ).first()
            if has_history:
                continue
            rows = _history_for(name, hcp.id)
            if rows:
                db.add_all(rows)
                added += len(rows)
        if added:
            await db.commit()

        print(f"Seed complete: {created} HCPs created, {added} interactions backfilled.")


if __name__ == "__main__":
    asyncio.run(seed())

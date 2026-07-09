"""Seeds a handful of demo HCPs (and light interaction history for one of
them) so the app isn't a blank slate on first run — makes the video demo
and `hcp_insights` tool meaningfully demonstrable immediately."""
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


async def seed():
    await init_db()
    async with AsyncSessionLocal() as db:
        existing = (await db.execute(select(HCP))).scalars().all()
        if existing:
            print(f"DB already has {len(existing)} HCPs — skipping seed.")
            return

        hcps = [HCP(**data) for data in DEMO_HCPS]
        db.add_all(hcps)
        await db.commit()
        for h in hcps:
            await db.refresh(h)

        mehta = hcps[0]
        history = [
            Interaction(
                hcp_id=mehta.id, interaction_type="visit", channel="structured",
                interaction_date=date.today() - timedelta(days=60), interaction_time="10:30",
                attendees=["Clinic nurse"],
                products_discussed=["Cardivax"], samples_dropped=["Cardivax 10mg"], materials_shared=["Cardivax efficacy deck"],
                topics_discussed="Introductory visit; discussed Cardivax efficacy data.",
                outcomes="HCP agreed to review the Phase III data before next visit.",
                summary="First meeting with Dr. Mehta; introduced Cardivax and shared Phase III efficacy data.",
                sentiment="neutral", follow_up_required=False,
            ),
            Interaction(
                hcp_id=mehta.id, interaction_type="visit", channel="structured",
                interaction_date=date.today() - timedelta(days=25), interaction_time="15:00",
                attendees=[],
                products_discussed=["Cardivax"], samples_dropped=["Cardivax 10mg", "Cardivax 20mg"], materials_shared=[],
                topics_discussed="Follow-up visit; HCP asked about elderly dosing safety data.",
                outcomes="HCP will consider broader prescribing pending elderly-dosing data.",
                summary="Dr. Mehta requested elderly-patient dosing safety data for Cardivax before prescribing more broadly.",
                sentiment="positive", follow_up_required=True, follow_up_notes="Send elderly dosing safety study PDF.",
            ),
        ]
        db.add_all(history)
        await db.commit()
        print(f"Seeded {len(hcps)} HCPs and {len(history)} interactions.")


if __name__ == "__main__":
    asyncio.run(seed())

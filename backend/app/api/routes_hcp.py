from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.models import HCP
from app.db.schemas import HCPCreate, HCPOut

router = APIRouter(prefix="/hcps", tags=["hcps"])


@router.get("", response_model=list[HCPOut])
async def list_hcps(db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(HCP).order_by(HCP.name))).scalars().all()
    return rows


@router.get("/{hcp_id}", response_model=HCPOut)
async def get_hcp(hcp_id: str, db: AsyncSession = Depends(get_db)):
    hcp = await db.get(HCP, hcp_id)
    if not hcp:
        raise HTTPException(404, "HCP not found")
    return hcp


@router.post("", response_model=HCPOut, status_code=201)
async def create_hcp(payload: HCPCreate, db: AsyncSession = Depends(get_db)):
    hcp = HCP(**payload.model_dump())
    db.add(hcp)
    await db.commit()
    await db.refresh(hcp)
    return hcp

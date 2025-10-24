from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from ..database import get_db
from ..auth import get_current_active_user
from .. import models_extended as models
from ..crud_summary import get_complete_business_summary

router = APIRouter(prefix="/api/summary", tags=["summary"])


@router.get("/business-overview")
def get_business_overview(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Obtiene un resumen completo e integral del negocio con datos reales"""
    try:
        # Convertir fechas si se proporcionan
        start_dt = datetime.fromisoformat(start_date) if start_date else None
        end_dt = datetime.fromisoformat(end_date) if end_date else None
        
        # Obtener resumen completo
        summary = get_complete_business_summary(
            db,
            current_user.organization_id,
            start_dt,
            end_dt
        )
        
        return summary
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Formato de fecha inválido: {str(e)}"
        )
    except Exception as e:
        print(f"Error en business-overview: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener resumen empresarial: {str(e)}"
        )
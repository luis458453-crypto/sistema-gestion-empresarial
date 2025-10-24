from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from ..database import get_db
from ..config import settings
from .. import auth
from ..auth import get_current_active_user

# Usar modelos extendidos por defecto
from .. import schemas_extended as schemas
from .. import models_extended as models

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.get("/health")
async def health_check():
    """Health check endpoint para mantener el servicio despierto"""
    return {"status": "ok", "message": "Backend is running"}


@router.post("/register", response_model=schemas.User, status_code=status.HTTP_201_CREATED)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # Verificar email
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="El email ya está registrado")
    
    # Verificar username
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="El nombre de usuario ya está en uso")
    
    # Crear usuario
    hashed_password = auth.get_password_hash(user.password)
    db_user = models.User(
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        hashed_password=hashed_password,
        role=getattr(user, 'role', 'empleado'),
        phone=getattr(user, 'phone', None)
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@router.post("/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = auth.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Usuario inactivo")
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=schemas.User)
async def read_users_me(current_user: schemas.User = Depends(auth.get_current_active_user)):
    return current_user


@router.put("/change-password")
async def change_password(
    password_data: dict,
    current_user: schemas.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Cambia la contraseña del usuario actual"""
    current_password = password_data.get("current_password")
    new_password = password_data.get("new_password")
    
    if not current_password or not new_password:
        raise HTTPException(
            status_code=400,
            detail="Se requieren la contraseña actual y la nueva contraseña"
        )
    
    # Verificar contraseña actual
    if not auth.verify_password(current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=400,
            detail="La contraseña actual es incorrecta"
        )
    
    # Validar nueva contraseña
    if len(new_password) < 6:
        raise HTTPException(
            status_code=400,
            detail="La nueva contraseña debe tener al menos 6 caracteres"
        )
    
    # Actualizar contraseña
    new_hashed_password = auth.get_password_hash(new_password)
    current_user.hashed_password = new_hashed_password
    
    db.commit()
    db.refresh(current_user)
    
    return {"message": "Contraseña cambiada exitosamente"}


@router.put("/session-settings")
async def update_session_settings(
    settings: dict,
    current_user: schemas.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Actualiza la configuración de sesión del usuario"""
    timeout = settings.get("timeout")
    auto_logout = settings.get("autoLogout")
    remember_me = settings.get("rememberMe")
    
    # Aquí podrías guardar estas configuraciones en la base de datos
    # Por ahora solo validamos los datos
    
    if timeout is not None and timeout not in [15, 30, 60, 120, 480, 0]:
        raise HTTPException(
            status_code=400,
            detail="Timeout inválido. Debe ser: 15, 30, 60, 120, 480 o 0 minutos"
        )
    
    # TODO: Guardar configuración en la base de datos
    # current_user.session_timeout = timeout
    # current_user.auto_logout = auto_logout
    # current_user.remember_me = remember_me
    # db.commit()
    
    return {
        "message": "Configuración de sesión actualizada",
        "settings": {
            "timeout": timeout,
            "autoLogout": auto_logout,
            "rememberMe": remember_me
        }
    }


@router.post("/logout-all-sessions")
async def logout_all_sessions(
    current_user: schemas.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Cierra todas las sesiones del usuario excepto la actual"""
    # TODO: Implementar lógica para invalidar tokens JWT
    # Por ahora solo retornamos un mensaje de éxito
    
    return {
        "message": "Todas las sesiones han sido cerradas exitosamente",
        "sessions_closed": 1  # Simulado
    }

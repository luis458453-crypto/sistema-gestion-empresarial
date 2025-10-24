"""
Utilidades para manejo de zona horaria
República Dominicana usa UTC-4 todo el año (no tiene horario de verano)
"""
from datetime import datetime, timezone, timedelta
from typing import Optional

# Zona horaria de República Dominicana (UTC-4)
RD_TIMEZONE = timezone(timedelta(hours=-4))


def get_rd_now() -> datetime:
    """
    Obtiene la fecha y hora actual en zona horaria de República Dominicana
    Returns:
        datetime: Fecha y hora actual en RD (UTC-4)
    """
    return datetime.now(RD_TIMEZONE)


def utc_to_rd(utc_datetime: datetime) -> datetime:
    """
    Convierte una fecha UTC a zona horaria de República Dominicana
    Args:
        utc_datetime: Fecha en UTC
    Returns:
        datetime: Fecha convertida a RD (UTC-4)
    """
    if utc_datetime is None:
        return None
    
    # Si no tiene timezone info, asumimos que es UTC
    if utc_datetime.tzinfo is None:
        utc_datetime = utc_datetime.replace(tzinfo=timezone.utc)
    
    return utc_datetime.astimezone(RD_TIMEZONE)


def rd_to_utc(rd_datetime: datetime) -> datetime:
    """
    Convierte una fecha de República Dominicana a UTC
    Args:
        rd_datetime: Fecha en RD (UTC-4)
    Returns:
        datetime: Fecha convertida a UTC
    """
    if rd_datetime is None:
        return None
    
    # Si no tiene timezone info, asumimos que es RD
    if rd_datetime.tzinfo is None:
        rd_datetime = rd_datetime.replace(tzinfo=RD_TIMEZONE)
    
    return rd_datetime.astimezone(timezone.utc)


def parse_date_string(date_string: str) -> Optional[datetime]:
    """
    Parsea un string de fecha y lo convierte a datetime en zona horaria RD
    Acepta formatos: YYYY-MM-DD, YYYY-MM-DD HH:MM:SS
    Args:
        date_string: String de fecha
    Returns:
        datetime: Fecha parseada en zona horaria RD, o None si el string es inválido
    """
    if not date_string:
        return None
    
    try:
        # Intentar parsear con hora
        if ' ' in date_string:
            dt = datetime.strptime(date_string, '%Y-%m-%d %H:%M:%S')
        else:
            # Solo fecha, establecer hora a medianoche
            dt = datetime.strptime(date_string, '%Y-%m-%d')
        
        # Asignar zona horaria RD
        return dt.replace(tzinfo=RD_TIMEZONE)
    except ValueError:
        return None


def format_datetime_rd(dt: datetime, include_time: bool = True) -> str:
    """
    Formatea un datetime para mostrar en zona horaria RD
    Args:
        dt: Datetime a formatear
        include_time: Si incluir la hora en el formato
    Returns:
        str: Fecha formateada
    """
    if dt is None:
        return ''
    
    # Convertir a zona horaria RD si no lo está
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    
    rd_dt = dt.astimezone(RD_TIMEZONE)
    
    if include_time:
        return rd_dt.strftime('%Y-%m-%d %H:%M:%S')
    else:
        return rd_dt.strftime('%Y-%m-%d')


def get_rd_date_range(start_date_str: Optional[str], end_date_str: Optional[str]) -> tuple:
    """
    Convierte strings de fecha a un rango de datetime en zona horaria RD
    Args:
        start_date_str: Fecha inicio (YYYY-MM-DD)
        end_date_str: Fecha fin (YYYY-MM-DD)
    Returns:
        tuple: (start_datetime, end_datetime) en zona horaria RD
    """
    start_dt = None
    end_dt = None
    
    if start_date_str:
        start_dt = parse_date_string(start_date_str)
        if start_dt:
            # Establecer a inicio del día (00:00:00)
            start_dt = start_dt.replace(hour=0, minute=0, second=0, microsecond=0)
    
    if end_date_str:
        end_dt = parse_date_string(end_date_str)
        if end_dt:
            # Establecer a fin del día (23:59:59)
            end_dt = end_dt.replace(hour=23, minute=59, second=59, microsecond=999999)
    
    return start_dt, end_dt

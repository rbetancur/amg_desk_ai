"""
Servicio de validaciones de negocio.
"""
from typing import Literal


def validate_state_transition(current: int, new: int) -> bool:
    """
    Valida si una transición de estado es permitida.
    
    Matriz de transiciones permitidas:
    - Pendiente (1) → En Trámite (2) ✅ Permitido
    - Pendiente (1) → Solucionado (3) ✅ Permitido (cierre directo)
    - En Trámite (2) → Solucionado (3) ✅ Permitido
    - Solucionado (3) → Pendiente (1) ❌ No permitido
    - Solucionado (3) → En Trámite (2) ❌ No permitido
    - Cualquier estado → mismo estado ✅ Permitido (no-op)
    
    Args:
        current: Estado actual (1, 2, o 3)
        new: Estado nuevo (1, 2, o 3)
        
    Returns:
        bool: True si la transición es permitida, False si no
        
    Raises:
        ValueError: Si los estados no son válidos (no son 1, 2, o 3)
    """
    valid_states = {1, 2, 3}
    
    if current not in valid_states:
        raise ValueError(f"Estado actual inválido: {current}. Estados válidos: {valid_states}")
    
    if new not in valid_states:
        raise ValueError(f"Estado nuevo inválido: {new}. Estados válidos: {valid_states}")
    
    # Mismo estado → mismo estado (no-op permitido)
    if current == new:
        return True
    
    # Transiciones permitidas
    allowed_transitions = {
        (1, 2),  # Pendiente → En Trámite
        (1, 3),  # Pendiente → Solucionado
        (2, 3),  # En Trámite → Solucionado
    }
    
    return (current, new) in allowed_transitions


#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import re

def analyze_errors():
    print("=" * 60)
    print("ANÁLISIS DE MENSAJES DE ERROR - BACKEND")
    print("=" * 60)
    
    # Analizar ValueError desde services/cita_service.py
    print("\n--- ValueError Messages desde src/services/cita_service.py ---")
    with open('src/services/cita_service.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    pattern = r'raise ValueError[^\)]+'
    matches = re.findall(pattern, content)
    
    categories = {
        "Fechas/Horas": [],
        "Servicios": [],
        "Barbero/Cliente": [],
        "Estados/Transiciones": [],
        "Horario": [],
        "Validación general": []
    }
    
    for m in matches:
        clean = m.replace('raise ValueError', '').replace('(', '').replace(')', '').strip()
        clean = clean.replace('"', '').replace("'", '').strip()
        
        lower = clean.lower()
        if "fecha" in lower or "hora" in lower:
            cat = "Fechas/Horas"
        elif "servicio" in lower:
            cat = "Servicios"
        elif "barbero" in lower or "cliente" in lower:
            cat = "Barbero/Cliente"
        elif "est" in lower or "complet" in lower or "cancel" in lower:
            cat = "Estados/Transiciones"
        elif "horario" in lower or "disponible" in lower or "atencion" in lower:
            cat = "Horario"
        else:
            cat = "Validación general"
        
        if cat in categories:
            categories[cat].append(clean)
    
    for cat, msgs in categories.items():
        print(f"\n[{cat}] ({len(msgs)} mensajes)")
        for msg in msgs[:4]:  # Mostrar hasta 4 por categoría
            print(f"    • {msg}")
        if len(msgs) > 4:
            print(f"    ... y {len(msgs)-4} más")
    
    # Analizar HTTPException desde routers
    print("\n--- HTTPException Messages desde src/routers/cita_router.py ---")
    try:
        with open('src/routers/cita_router.py', 'r', encoding='utf-8') as f:
            router = f.read()
        
        pattern2 = r'raise HTTPException\(status_code=(\d+), detail="([^"]+)"'
        exceptions = re.findall(pattern2, router)
        
        print(f"\nTotal HTTPExceptions encontrados: {len(exceptions)}")
        for code, detail in exceptions:
            print(f"  Status {code}: {detail}")
    except FileNotFoundError:
        print("Archivo router no encontrado")
    
    # Summary
    print("\n" + "=" * 60)
    print("RESUMEN")
    print("=" * 60)
    total_errors = sum(len(v) for v in categories.values()) + len(exceptions) if 'exceptions' in dir() else 0
    print(f"Total mensajes de error identificados: {total_errors}")
    print("Categorías con más mensajes:")
    for cat, msgs in sorted(categories.items(), key=lambda x: len(x[1]), reverse=True):
        print(f"  {cat}: {len(msgs)}")

if __name__ == "__main__":
    analyze_errors()
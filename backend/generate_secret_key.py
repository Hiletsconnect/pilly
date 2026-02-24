#!/usr/bin/env python3
"""
Script para generar SECRET_KEY seguro para JWT
Ejecutar: python generate_secret_key.py
"""

import secrets

if __name__ == "__main__":
    secret_key = secrets.token_urlsafe(32)
    print("\n" + "="*60)
    print("🔐 SECRET_KEY Generado:")
    print("="*60)
    print(f"\nSECRET_KEY={secret_key}\n")
    print("="*60)
    print("\n⚠️  IMPORTANTE:")
    print("1. Copia este SECRET_KEY")
    print("2. Agrégalo a las variables de entorno en Railway")
    print("3. NUNCA lo compartas públicamente")
    print("4. Usa uno diferente para desarrollo y producción")
    print("\n")

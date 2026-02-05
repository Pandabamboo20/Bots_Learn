# Bots Learn NES

Aplicación base en Python para entrenar múltiples bots por generaciones y aprender a completar juegos de NES desde el inicio de cada partida.

## Características

- Carga de ROMs (.nes) y presets de controles en formato JSON.
- Motor de evolución simple con selección, cruces y mutaciones por generación.
- Vista del bot líder con detalles de élites, métricas promedio y vista en vivo.
- Ventana gráfica estilo panel HTML con estado en tiempo real.
- Tutorial integrado para crear, importar y exportar presets.

## Requisitos

- Python 3.10+
- Tkinter (incluido en la mayoría de instalaciones de Python)

## Uso

```bash
python app/main.py
```

1. Selecciona la ROM original del juego.
2. Importa un preset JSON o usa el preset por defecto de Super Mario Bros.
3. Ajusta la cantidad de bots por generación.
4. Inicia el entrenamiento y observa el bot líder.

## Notas

El módulo de emulación incluido sigue siendo una implementación local, pero ahora expone validación de ROM, métricas y resultados por bot. Sustituye `EmulatorSession` por un adaptador real (por ejemplo, Mesen o FCEUX mediante bindings) para ejecutar la ROM de manera fiel.

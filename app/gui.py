import json
import threading
import tkinter as tk
from dataclasses import asdict
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from bots import BotPopulation, GenerationResult
from emulation import EmulatorSession
from presets import ControlPreset, PresetLibrary
from tutorial import TutorialContent


class MarioBotsApp:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("Bots Learn NES")
        self.root.geometry("1100x700")
        self.root.configure(bg="#0f111a")
        self.style = ttk.Style(self.root)
        self.style.theme_use("clam")
        self.style.configure("TFrame", background="#0f111a")
        self.style.configure("TLabel", background="#0f111a", foreground="#e6e6e6")
        self.style.configure("Header.TLabel", font=("Helvetica", 16, "bold"))
        self.style.configure("SubHeader.TLabel", font=("Helvetica", 12, "bold"))
        self.style.configure("TButton", background="#1f6feb", foreground="#ffffff")

        self.rom_path: str | None = None
        self.preset_path: str | None = None
        self.current_preset: ControlPreset | None = None
        self.bot_count = tk.IntVar(value=500)
        self.population: BotPopulation | None = None
        self.session: EmulatorSession | None = None
        self.run_thread: threading.Thread | None = None
        self.is_running = False
        self.latest_summary = "Sin ejecución en progreso."
        self.latest_details = ""
        self.frame_index = 0
        self.frame_snapshots = []

        self._build_layout()

    def run(self) -> None:
        self.root.mainloop()

    def _build_layout(self) -> None:
        container = ttk.Frame(self.root, padding=24)
        container.pack(fill=tk.BOTH, expand=True)

        header = ttk.Label(
            container,
            text="Sistema de Aprendizaje Generacional para NES",
            style="Header.TLabel",
        )
        header.pack(anchor=tk.W)

        description = ttk.Label(
            container,
            text=(
                "Entrena millones de bots para completar juegos de NES desde el inicio. "
                "Importa una ROM y un preset de controles para ejecutar el entrenamiento."
            ),
            wraplength=900,
        )
        description.pack(anchor=tk.W, pady=(6, 24))

        form_frame = ttk.Frame(container)
        form_frame.pack(fill=tk.X)

        rom_row = ttk.Frame(form_frame)
        rom_row.pack(fill=tk.X, pady=6)
        ttk.Label(rom_row, text="ROM del juego (.nes)").pack(side=tk.LEFT)
        self.rom_label = ttk.Label(rom_row, text="Sin seleccionar", width=60)
        self.rom_label.pack(side=tk.LEFT, padx=8)
        ttk.Button(rom_row, text="Elegir", command=self._select_rom).pack(side=tk.LEFT)

        preset_row = ttk.Frame(form_frame)
        preset_row.pack(fill=tk.X, pady=6)
        ttk.Label(preset_row, text="Preset de controles").pack(side=tk.LEFT)
        self.preset_label = ttk.Label(preset_row, text="Sin seleccionar", width=60)
        self.preset_label.pack(side=tk.LEFT, padx=8)
        ttk.Button(preset_row, text="Importar", command=self._select_preset).pack(side=tk.LEFT)
        ttk.Button(
            preset_row,
            text="Usar preset SMB",
            command=self._use_default_preset,
        ).pack(side=tk.LEFT, padx=6)
        ttk.Button(
            preset_row,
            text="Exportar preset",
            command=self._export_preset,
        ).pack(side=tk.LEFT)

        bots_row = ttk.Frame(form_frame)
        bots_row.pack(fill=tk.X, pady=6)
        ttk.Label(bots_row, text="Bots por generación").pack(side=tk.LEFT)
        ttk.Entry(bots_row, textvariable=self.bot_count, width=12).pack(
            side=tk.LEFT, padx=8
        )
        ttk.Label(bots_row, text="(recomendado 500)").pack(side=tk.LEFT)

        controls_row = ttk.Frame(form_frame)
        controls_row.pack(fill=tk.X, pady=(16, 6))
        ttk.Button(
            controls_row,
            text="Iniciar entrenamiento",
            command=self._start_training,
        ).pack(side=tk.LEFT)
        ttk.Button(
            controls_row,
            text="Detener",
            command=self._stop_training,
        ).pack(side=tk.LEFT, padx=8)

        content_frame = ttk.Frame(container)
        content_frame.pack(fill=tk.BOTH, expand=True, pady=(16, 0))

        left_panel = ttk.Frame(content_frame)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 16))
        right_panel = ttk.Frame(content_frame, width=280)
        right_panel.pack(side=tk.RIGHT, fill=tk.Y)

        ttk.Label(left_panel, text="Vista del bot líder", style="SubHeader.TLabel").pack(
            anchor=tk.W
        )
        self.canvas = tk.Canvas(
            left_panel,
            background="#1b1f2a",
            highlightthickness=0,
            height=360,
        )
        self.canvas.pack(fill=tk.BOTH, expand=True, pady=(8, 0))
        self.canvas_text = self.canvas.create_text(
            20,
            20,
            anchor=tk.NW,
            fill="#9cf5ff",
            font=("Consolas", 12),
            text="Carga una ROM para iniciar el entrenamiento.",
        )

        ttk.Label(right_panel, text="Estado", style="SubHeader.TLabel").pack(anchor=tk.W)
        self.status_text = tk.Text(
            right_panel,
            height=16,
            wrap=tk.WORD,
            background="#0b0e16",
            foreground="#d1d5db",
            borderwidth=0,
        )
        self.status_text.pack(fill=tk.BOTH, expand=True, pady=(8, 16))
        self.status_text.insert(tk.END, "Sin ejecución en progreso.\n")

        ttk.Label(right_panel, text="Tutorial", style="SubHeader.TLabel").pack(anchor=tk.W)
        tutorial = TutorialContent().render()
        tutorial_label = ttk.Label(
            right_panel, text=tutorial, wraplength=260, foreground="#b4b4b4"
        )
        tutorial_label.pack(anchor=tk.W, pady=(8, 0))

    def _select_rom(self) -> None:
        rom = filedialog.askopenfilename(
            title="Selecciona la ROM", filetypes=[("NES ROM", "*.nes")]
        )
        if not rom:
            return
        self.rom_path = rom
        self.rom_label.config(text=rom)

    def _select_preset(self) -> None:
        preset = filedialog.askopenfilename(
            title="Selecciona el preset",
            filetypes=[("Preset JSON", "*.json")],
        )
        if not preset:
            return
        self.preset_path = preset
        preset_data = PresetLibrary.load_from_path(preset)
        self.current_preset = ControlPreset.from_dict(preset_data)
        self.preset_label.config(text=preset)

    def _use_default_preset(self) -> None:
        self.current_preset = PresetLibrary.default_super_mario_bros()
        self.preset_path = None
        self.preset_label.config(text="Preset interno: Super Mario Bros")

    def _export_preset(self) -> None:
        if not self.current_preset:
            messagebox.showwarning(
                "Sin preset",
                "Carga o selecciona un preset antes de exportarlo.",
            )
            return
        destination = filedialog.asksaveasfilename(
            title="Guardar preset",
            defaultextension=".json",
            filetypes=[("Preset JSON", "*.json")],
        )
        if not destination:
            return
        PresetLibrary.save(destination, self.current_preset)
        messagebox.showinfo("Preset guardado", f"Preset exportado en {destination}.")

    def _start_training(self) -> None:
        if self.is_running:
            messagebox.showinfo("Entrenamiento", "El entrenamiento ya está en curso.")
            return
        if not self.rom_path or not (self.preset_path or self.current_preset):
            messagebox.showwarning(
                "Configuración incompleta",
                "Selecciona una ROM y un preset antes de iniciar.",
            )
            return
        if not Path(self.rom_path).exists():
            messagebox.showerror("ROM inválida", "No se encontró la ROM indicada.")
            return
        if Path(self.rom_path).suffix.lower() != ".nes":
            messagebox.showerror(
                "ROM inválida",
                "La ROM debe tener extensión .nes.",
            )
            return

        try:
            bot_count = int(self.bot_count.get())
        except ValueError:
            messagebox.showerror("Entrada inválida", "Indica un número válido de bots.")
            return
        if bot_count <= 0:
            messagebox.showerror("Entrada inválida", "El número de bots debe ser mayor a 0.")
            return

        if self.current_preset:
            preset = self.current_preset
        else:
            preset_data = PresetLibrary.load_from_path(self.preset_path or "")
            preset = ControlPreset.from_dict(preset_data)
            self.current_preset = preset

        self.population = BotPopulation(bot_count=bot_count, preset=preset)
        self.session = EmulatorSession(self.rom_path, preset)

        self.status_text.delete("1.0", tk.END)
        self.status_text.insert(tk.END, "Inicializando generación 1...\n")
        self.latest_summary = "Inicializando generación 1..."
        self.latest_details = ""
        self._append_status(
            f"ROM: {self.session.rom_info.name} "
            f"({self.session.rom_info.size_kb} KB) "
            f"{'OK' if self.session.rom_info.valid_header else 'Sin cabecera NES'}\n"
        )
        self._append_status(
            f"Preset: {preset.game_title} - {preset.description}\n"
        )
        self.canvas.itemconfig(
            self.canvas_text, text="Preparando la simulación en paralelo..."
        )

        self.is_running = True
        self._schedule_frame_updates()
        self.run_thread = threading.Thread(target=self._run_training_loop, daemon=True)
        self.run_thread.start()

    def _stop_training(self) -> None:
        if not self.is_running:
            return
        self.is_running = False
        if self.session:
            self.session.stop()
        self._append_status("Entrenamiento detenido por el usuario.\n")

    def _run_training_loop(self) -> None:
        generation_index = 1
        while self.is_running and self.population and self.session:
            result = self.population.run_generation(self.session, generation_index)
            self._update_generation(result)
            generation_index += 1
            if result.goal_reached:
                self.is_running = False

    def _update_generation(self, result: GenerationResult) -> None:
        summary = (
            f"Generación {result.generation}: "
            f"mejor distancia {result.best_distance} - "
            f"tiempo {result.best_time}s - "
            f"promedio {result.avg_distance} - "
            f"tasa de éxito {result.success_rate:.0%}\n"
        )
        elite_payload = [asdict(state) for state in result.elite_states]
        details = json.dumps(
            {
                "leader": asdict(result.leader_state),
                "elite": elite_payload,
            },
            ensure_ascii=False,
            indent=2,
        )

        self.root.after(
            0,
            lambda: self._render_generation(summary, details, result.goal_reached),
        )

    def _render_generation(self, summary: str, details: str, goal_reached: bool) -> None:
        self.latest_summary = summary.strip()
        self.latest_details = details
        self._append_status(summary)
        self._render_live_frame()
        if goal_reached:
            self._append_status("Objetivo alcanzado. Fin del entrenamiento.\n")
            messagebox.showinfo(
                "Entrenamiento completado",
                "El bot líder completó el juego de manera óptima.",
            )

    def _append_status(self, text: str) -> None:
        self.status_text.insert(tk.END, text)
        self.status_text.see(tk.END)

    def _schedule_frame_updates(self) -> None:
        if not self.is_running:
            return
        self._render_live_frame()
        self.root.after(350, self._schedule_frame_updates)

    def _render_live_frame(self) -> None:
        if not self.session:
            return
        if not self.frame_snapshots or self.frame_index >= len(self.frame_snapshots):
            self.frame_snapshots = self.session.get_leader_frames()
            self.frame_index = 0
        snapshot = self.frame_snapshots[self.frame_index]
        self.frame_index += 1
        frame_text = (
            f"{self.latest_summary}\n"
            f"Vista en vivo: {snapshot.viewport}\n"
            f"Inputs: {', '.join(snapshot.inputs)}\n\n"
            f"Estado del bot líder:\n{self.latest_details}"
        )
        self.canvas.itemconfig(self.canvas_text, text=frame_text)

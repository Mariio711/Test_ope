# Programa interactivo para responder preguntas tipo test desde archivos CSV
# Autor: GitHub Copilot

import csv
import os
import random
import sys
import platform
import json
import sqlite3
from datetime import datetime
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk

class TestApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Test Interactivo Profesional")
        self.root.geometry("900x700")
        self.root.minsize(800, 600)
        
        # Colores Tema Rosa Pastel
        self.bg_color = "#FFF0F5"       # LavenderBlush
        self.accent_color = "#FFB7C5"   # Pastel Pink cherry blossom
        self.button_color = "#FFC0CB"   # Pink
        self.text_color = "#5c3a4d"     # Darker pink/purple for text readability
        
        # Variables de Configuración
        self.font_size = 12
        self.mezclar_respuestas = tk.BooleanVar(value=False)
        self.mapa_respuestas_desordenadas = {} # Para rastrear el índice real cuando se desordenan

        # Configuración de estilos
        style = ttk.Style()
        style.theme_use('clam')
        
        # Estilos personalizados (Base)
        style.configure("TFrame", background=self.bg_color)
        style.configure("TLabelframe", background=self.bg_color, foreground=self.text_color)
        style.configure("TLabelframe.Label", background=self.bg_color, foreground=self.text_color)
        style.configure("TLabel", background=self.bg_color, foreground=self.text_color)
        style.configure("TButton", background=self.button_color, foreground=self.text_color, borderwidth=1)
        style.map("TButton", background=[('active', '#FF69B4')]) # HotPink on hover
        style.configure("TCheckbutton", background=self.bg_color, foreground=self.text_color)
        style.configure("TRadiobutton", background=self.bg_color, foreground=self.text_color)
        
        self.update_styles() # Método para aplicar fuentes
        
        self.root.configure(bg=self.bg_color)

        self.preguntas = []
        self.preguntas_seleccionadas = []
        self.respuestas_usuario = [] # Ahora guardará el índice original (1,2,3,4)
        self.idx_pregunta = 0
        self.cantidad = 0
        self.mezclar = tk.BooleanVar()
        self.vars_archivos = {}
        
        self.setup_inicio()

    def update_styles(self):
        style = ttk.Style()
        base_fs = self.font_size
        
        style.configure("Title.TLabel", font=("Helvetica", base_fs + 8, "bold"), foreground=self.text_color)
        style.configure("Subtitle.TLabel", font=("Helvetica", base_fs + 2), foreground=self.text_color)
        style.configure("Question.TLabel", font=("Helvetica", base_fs + 4), padding=10, foreground=self.text_color)
        style.configure("Result.TLabel", font=("Helvetica", base_fs))
        style.configure("Action.TButton", font=("Helvetica", base_fs, "bold"), padding=5, background=self.accent_color)
        style.configure("TLabel", font=("Helvetica", base_fs))
        style.configure("TButton", font=("Helvetica", base_fs))
        style.configure("TRadiobutton", font=("Helvetica", base_fs))
        style.configure("TCheckbutton", font=("Helvetica", base_fs))

    def cambiar_tamano_fuente(self, delta):
        nuevan_tam = self.font_size + delta
        if 8 <= nuevan_tam <= 24:
            self.font_size = nuevan_tam
            self.update_styles()
            # Si estamos mostrando una pregunta, recargarla para aplicar cambios
            if hasattr(self, 'preguntas_seleccionadas') and self.preguntas_seleccionadas and self.idx_pregunta < len(self.preguntas_seleccionadas):
                self.mostrar_pregunta()

    def setup_inicio(self):
        self.limpiar_ventana()

        # Contenedor principal
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill="both", expand=True)

        # === ZONA INFERIOR (Botones y Config) - Pack primero para asegurar visibilidad ===
        bottom_area = ttk.Frame(main_frame)
        bottom_area.pack(side="bottom", fill="x", pady=10)

        # Botón Historial
        ttk.Button(bottom_area, text="📂 Ver Historial de Intentos", command=self.ver_historial).pack(side="bottom", fill="x", pady=(0, 5))

        # Botón de inicio
        ttk.Button(bottom_area, text="COMENZAR EXAMEN", style="Action.TButton", command=self.comenzar).pack(side="bottom", fill="x", ipadx=40, ipady=10, pady=10)

        # Opciones (Encima de los botones)
        opt_frame = ttk.LabelFrame(bottom_area, text="Configuración", padding="10")
        opt_frame.pack(side="bottom", fill="x", pady=10)
        
        ttk.Checkbutton(opt_frame, text="Mezclar orden de preguntas aleatoriamente", variable=self.mezclar).pack(anchor="w")
        ttk.Checkbutton(opt_frame, text="Desordenar opciones de respuesta (a, b, c, d...)", variable=self.mezclar_respuestas).pack(anchor="w")


        # === ZONA SUPERIOR (Título) ===
        # Título
        ttk.Label(main_frame, text="Bienvenido al Test Interactivo", style="Title.TLabel").pack(side="top", pady=(0, 10))


        # === ZONA CENTRAL (Selección de Archivos - Flexible) ===
        # Sección de selección de archivos
        lbl_frame = ttk.LabelFrame(main_frame, text="Fuente de Preguntas", padding="10")
        lbl_frame.pack(side="top", fill="both", expand=True, pady=5)
        
        # Botones de control de archivos (Pack BOTTOM dentro del frame para asegurar visibilidad)
        btn_frame = ttk.Frame(lbl_frame)
        btn_frame.pack(side="bottom", fill="x", pady=5)
        
        ttk.Button(btn_frame, text="Buscar Externos...", command=self.buscar_otros_archivos).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Todos", command=self.seleccionar_todos).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Ninguno", command=self.deseleccionar_todos).pack(side="left", padx=5)

        ttk.Label(lbl_frame, text="Selecciona archivos CSV disponibles:", style="Subtitle.TLabel").pack(side="top", anchor="w", pady=(0, 5))

        # Frame con Scrollbar para lista de archivos (Pack expandible ocupa el resto)
        list_frame = ttk.Frame(lbl_frame, relief="sunken", borderwidth=1)
        list_frame.pack(side="top", fill="both", expand=True, pady=5)

        self.canvas_files = tk.Canvas(list_frame, bg="white", highlightthickness=0)
        scroll_files = ttk.Scrollbar(list_frame, orient="vertical", command=self.canvas_files.yview)
        
        self.frame_checks = ttk.Frame(self.canvas_files)
        # Style helper for white background frame inside canvas
        s = ttk.Style()
        s.configure("White.TFrame", background="white")
        self.frame_checks.configure(style="White.TFrame")
        
        window_id = self.canvas_files.create_window((0, 0), window=self.frame_checks, anchor="nw")
        
        def configure_scroll_region(event):
            self.canvas_files.configure(scrollregion=self.canvas_files.bbox("all"))
            
        def configure_window_width(event):
            self.canvas_files.itemconfig(window_id, width=event.width)

        self.frame_checks.bind("<Configure>", configure_scroll_region)
        self.canvas_files.bind("<Configure>", configure_window_width)

        self.canvas_files.configure(yscrollcommand=scroll_files.set)

        self.canvas_files.pack(side="left", fill="both", expand=True)
        scroll_files.pack(side="right", fill="y")
        
        # Bind MouseWheel for macOS trackpad
        def _on_mousewheel(event):
            self.canvas_files.yview_scroll(int(-1*(event.delta)), "units")
        
        # Vincular tanto al canvas como al frame interno para asegurar captura
        self.canvas_files.bind_all("<MouseWheel>", _on_mousewheel)
        self.frame_checks.bind("<MouseWheel>", _on_mousewheel)
        
        # Cargar archivos automáticamente
        self.cargar_archivos_carpeta()

    def cargar_archivos_carpeta(self):
        # Limpiar anteriores si recarga
        for widget in self.frame_checks.winfo_children():
            widget.destroy()
        self.vars_archivos = {} 

        rutas_a_buscar = []
        
        try:
            # 1. Ruta base del ejecutable o script
            if getattr(sys, 'frozen', False):
                ruta_ejecutable = sys.executable
                if platform.system() == 'Darwin' and '.app' in ruta_ejecutable:
                    # Subir desde Contents/MacOS/Exe hasta la carpeta contenedora del .app
                    ruta_base = os.path.dirname(os.path.dirname(os.path.dirname(ruta_ejecutable)))
                else:
                    ruta_base = os.path.dirname(ruta_ejecutable)
            else:
                ruta_base = os.path.dirname(os.path.abspath(__file__))
            
            rutas_a_buscar.append(("Ubicación del Programa", ruta_base))

            # 2. Carpeta Documentos/TestInteractivo (historial y banco de preguntas personal)
            docs_dir = os.path.join(os.path.expanduser("~"), "Documents", "TestInteractivo")
            if os.path.exists(docs_dir):
                rutas_a_buscar.append(("Mis Documentos/TestInteractivo", docs_dir))
            else:
                # Si no existe, la creamos silenciosamente para que el usuario pueda poner cosas ahí
                try: os.makedirs(docs_dir, exist_ok=True)
                except: pass

            found_total = 0

            for nombre_ubicacion, ruta in rutas_a_buscar:
                if not os.path.exists(ruta): continue
                
                archivos = [f for f in os.listdir(ruta) if f.lower().endswith('.csv')]
                archivos.sort()
                
                if archivos:
                    # Separador visual si hay múltiples orígenes
                    if found_total > 0:
                        ttk.Separator(self.frame_checks, orient="horizontal").pack(fill="x", pady=5)
                    
                    ttk.Label(self.frame_checks, text=f"📂 {nombre_ubicacion}:", font=("Helvetica", 9, "bold"), background="white", foreground="#555").pack(anchor="w", padx=5, pady=(5,0))
                    
                    for archivo in archivos:
                        ruta_completa = os.path.join(ruta, archivo)
                        self.agregar_check_archivo(ruta_completa, os.path.basename(archivo))
                        found_total += 1

            if found_total == 0:
                msg = f"No se encontraron archivos CSV en:\n\n"
                for n, r in rutas_a_buscar:
                    msg += f"• {n}\n  ({r})\n\n"
                msg += "Usa 'Buscar Externos' para seleccionar archivos manualmente."
                ttk.Label(self.frame_checks, text=msg, background="white", wraplength=350).pack(padx=10, pady=10)
                
        except Exception as e:
            messagebox.showerror("Error", f"Error al leer carpetas: {e}")

    def agregar_check_archivo(self, ruta, nombre, seleccionado=False):
        if ruta not in self.vars_archivos:
            var = tk.BooleanVar(value=seleccionado)
            chk = ttk.Checkbutton(self.frame_checks, text=nombre, variable=var, style="TCheckbutton")
            chk.pack(fill="x", anchor="w", padx=10, pady=2)
            self.vars_archivos[ruta] = var

    def buscar_otros_archivos(self):
        archivos = filedialog.askopenfilenames(filetypes=[("Archivos CSV", "*.csv")])
        if archivos:
            for archivo in archivos:
                self.agregar_check_archivo(archivo, f"{os.path.basename(archivo)} (Externo)", seleccionado=True)

    def seleccionar_todos(self):
        for var in self.vars_archivos.values(): var.set(True)

    def deseleccionar_todos(self):
        for var in self.vars_archivos.values(): var.set(False)

    def comenzar(self):
        self.limpiar_bindings() # Limpiar rueda ratón previa
        
        archivos_seleccionados = [ruta for ruta, var in self.vars_archivos.items() if var.get()]
        if not archivos_seleccionados:
            messagebox.showwarning("Atención", "Por favor, selecciona al menos un archivo de preguntas.")
            return

        try:
            self.preguntas = cargar_preguntas_desde_archivos(archivos_seleccionados)
        except Exception as e:
            messagebox.showerror("Error Crítico", f"No se pudieron cargar las preguntas:\n{e}")
            return

        if not self.preguntas:
            messagebox.showerror("Error", "No se encontraron preguntas válidas en los archivos seleccionados.\nVerifica el formato del CSV (debe tener cabeceras).")
            return

        max_preg = len(self.preguntas)
        
        # Diálogo personalizado o simpledialog mejorado
        cantidad = simpledialog.askinteger("Configuración", f"Se encontraron {max_preg} preguntas.\n¿Cuántas deseas responder?", 
                                         parent=self.root, minvalue=1, maxvalue=max_preg)
        
        if not cantidad:
            return

        self.cantidad = cantidad
        self.preguntas_seleccionadas = seleccionar_preguntas(self.preguntas, self.cantidad, self.mezclar.get())
        
        # Inicializamos la lista con Nones para poder ir y venir
        self.respuestas_usuario = [None] * self.cantidad
        
        self.idx_pregunta = 0
        self.mostrar_pregunta()

    def mostrar_pregunta(self):
        self.limpiar_ventana()

        if self.idx_pregunta >= self.cantidad:
            self.mostrar_correccion()
            return

        pregunta = self.preguntas_seleccionadas[self.idx_pregunta]
        
        # === Header: Barra de progreso y Controles ===
        header_frame = ttk.Frame(self.root, padding="10")
        header_frame.pack(side="top", fill="x")
        
        # === Botones de navegación Footer (Pack FIRST to ensure visibility) ===
        nav_frame = ttk.Frame(self.root, padding="15", relief="raised")
        nav_frame.pack(side="bottom", fill="x")

        # === Contenido Pregunta (Pack LAST to fill remaining space) ===
        content_frame = ttk.Frame(self.root, padding="20")
        content_frame.pack(side="top", fill="both", expand=True)
        
        top_info = ttk.Frame(header_frame)
        top_info.pack(fill="x")
        
        # Info Pregunta
        ttk.Label(top_info, text=f"Pregunta {self.idx_pregunta + 1} de {self.cantidad}", font=("Helvetica", self.font_size, "bold"), foreground=self.text_color).pack(side="left")
        
        # Controles Fuente (Derecha arriba)
        font_frame = ttk.Frame(top_info)
        font_frame.pack(side="right")
        ttk.Button(font_frame, text="A-", width=3, command=lambda: self.cambiar_tamano_fuente(-1)).pack(side="left", padx=2)
        ttk.Button(font_frame, text="A+", width=3, command=lambda: self.cambiar_tamano_fuente(1)).pack(side="left", padx=2)
        
        # Barra Progreso
        progress = ttk.Progressbar(header_frame, maximum=self.cantidad, value=self.idx_pregunta + 1, length=100)
        progress.pack(fill="x", pady=(5,0))
        
        # Selector de Pregunta (Jump to)
        nav_select_frame = ttk.Frame(header_frame, padding=(0,5))
        nav_select_frame.pack(fill="x")
        ttk.Label(nav_select_frame, text="Ir a pregunta:").pack(side="left")
        
        opciones_combo = [f"{i+1}" for i in range(self.cantidad)]
        combo_preg = ttk.Combobox(nav_select_frame, values=opciones_combo, width=5, state="readonly")
        combo_preg.set(str(self.idx_pregunta + 1))
        combo_preg.pack(side="left", padx=5)
        combo_preg.bind("<<ComboboxSelected>>", lambda e: self.saltar_a_pregunta(int(combo_preg.get()) - 1))
        
        ttk.Label(top_info, text=f" | Fuente: {pregunta.get('archivo_origen', '-')}", font=("Helvetica", max(8, self.font_size-4)), foreground="#777").pack(side="right", padx=10)


        # === Contenido Pregunta ===
        content_frame = ttk.Frame(self.root, padding="20")
        content_frame.pack(fill="both", expand=True)

        txt_pregunta = pregunta.get('pregunta', 'Error: Pregunta sin texto')
        lbl_preg = ttk.Label(content_frame, text=f"{self.idx_pregunta + 1}. {txt_pregunta}", style="Question.TLabel", wraplength=800)
        lbl_preg.pack(pady=(0, 20), anchor="w", fill="x")
        
        # Ajuste dinámico del wraplength
        lbl_preg.bind("<Configure>", lambda e: lbl_preg.configure(wraplength=e.width - 20))

        # === Opciones (Scrollable) ===
        # Recuperar respuesta guardada si existe
        resp_actual = self.respuestas_usuario[self.idx_pregunta]
        
        self.resp_var = tk.IntVar(value=0) # Valor visual (del 1 al N según orden en pantalla)
        
        # Frame central expansible con scroll
        central_frame = ttk.Frame(content_frame)
        central_frame.pack(fill="both", expand=True)

        opciones_canvas = tk.Canvas(central_frame, bg=self.bg_color, highlightthickness=0)
        opciones_scroll = ttk.Scrollbar(central_frame, orient="vertical", command=opciones_canvas.yview)
        
        opciones_inner = ttk.Frame(opciones_canvas)
        # Importante: Window width dinámico
        window_id = opciones_canvas.create_window((0, 0), window=opciones_inner, anchor="nw")
        
        opciones_opciones = obtener_opciones(pregunta)
        
        # Lógica de Desordenar Opciones
        if self.mezclar_respuestas.get():
            # Si mezclamos, necesitamos guardar el mapeo para esta pregunta específica
            if self.idx_pregunta not in self.mapa_respuestas_desordenadas:
                # Crear una permutación (tupla de (indice_real_original, texto))
                items_con_indice = list(enumerate(opciones_opciones, 1)) # [(1, txtA), (2, txtB)...]
                random.shuffle(items_con_indice)
                self.mapa_respuestas_desordenadas[self.idx_pregunta] = items_con_indice
            
            # Usar el orden guardado
            items_a_mostrar = self.mapa_respuestas_desordenadas[self.idx_pregunta]
        else:
            # Orden normal
            items_a_mostrar = list(enumerate(opciones_opciones, 1))
            self.mapa_respuestas_desordenadas[self.idx_pregunta] = items_a_mostrar # Guardar también el normal por consistencia

        # Configurar variable si ya había respuesta
        if resp_actual is not None:
             # Buscar qué posición visual corresponde al índice real guardado (resp_actual)
             for idx_vis, (idx_real, _) in enumerate(items_a_mostrar, 1):
                 if idx_real == resp_actual:
                     self.resp_var.set(idx_vis)
                     break

        # Renderizar opciones con WRAP LENGTH DINÁMICO
        self.radio_labels = [] # Guardar referencias para actualizarlos
        for idx_visual, (idx_real_original, texto_opcion) in enumerate(items_a_mostrar, 1):
            # idx_visual es el valor que asume el Radiobutton (1, 2, 3...)
            # Usamos un Frame por opción para controlar mejor el layout de texto largo
            row = ttk.Frame(opciones_inner)
            row.pack(fill="x", pady=5, padx=5)
            
            rb = ttk.Radiobutton(row, variable=self.resp_var, value=idx_visual, style="TRadiobutton")
            rb.pack(side="left", anchor="n", pady=2)
            
            # Label separado para texto con wrap
            lbl = ttk.Label(row, text=texto_opcion, font=("Helvetica", self.font_size))
            lbl.pack(side="left", fill="x", expand=True, padx=5)
            # Hacer clic en el texto también selecciona
            lbl.bind("<Button-1>", lambda e, v=idx_visual: self.resp_var.set(v))
            
            self.radio_labels.append(lbl)

        # Ajuste de scroll y wrap automático
        def on_canvas_configure(event):
            canvas_width = event.width
            opciones_canvas.itemconfig(window_id, width=canvas_width)
            # Actualizar wraplength de todas las opciones
            wrap_limit = max(200, canvas_width - 60) # Margen para el radio y scroll
            for lbl in self.radio_labels:
                lbl.configure(wraplength=wrap_limit)
        
        opciones_inner.bind("<Configure>", lambda e: opciones_canvas.configure(scrollregion=opciones_canvas.bbox("all")))
        opciones_canvas.bind("<Configure>", on_canvas_configure)
        opciones_canvas.configure(yscrollcommand=opciones_scroll.set)
        
        opciones_canvas.pack(side="left", fill="both", expand=True)
        opciones_scroll.pack(side="right", fill="y")

        # Bind MouseWheel for Options (macOS trackpad)
        def _on_opciones_scroll(event):
            try:
                opciones_canvas.yview_scroll(int(-1*(event.delta)), "units")
            except: pass
            
        # Atar evento globalmente para esta pantalla
        opciones_canvas.bind_all("<MouseWheel>", _on_opciones_scroll)

        # Configurar Footer (Ya creado al inicio para garantizar visibilidad)
        
        # Grid layout para footer responsive
        nav_frame.columnconfigure(0, weight=1) # Espacio flexible
        nav_frame.columnconfigure(1, weight=0) # Botones centro/der
        
        # Botones Izquierda (Anterior)
        if self.idx_pregunta > 0:
            ttk.Button(nav_frame, text="<< Anterior", command=self.pregunta_anterior).grid(row=0, column=0, sticky="w")

        # Contenedor derecha (Blanco + Siguiente)
        right_group = ttk.Frame(nav_frame)
        right_group.grid(row=0, column=1, sticky="e")
        
        ttk.Button(right_group, text="Dejar en blanco", command=lambda: self.guardar_respuesta_actual(None)).pack(side="left", padx=5)
        
        # Botón Siguiente / Finalizar
        txt_siguiente = "Siguiente >>" if self.idx_pregunta < self.cantidad - 1 else "Finalizar Examen"
        ttk.Button(right_group, text=txt_siguiente, style="Action.TButton", command=self.siguiente_pregunta_accion).pack(side="left")

    def siguiente_pregunta_accion(self):
        val_visual = self.resp_var.get()
        if val_visual == 0:
            if messagebox.askyesno("Sin selección", "¿Deseas dejar esta pregunta en blanco y continuar?"):
                self.guardar_respuesta_actual(None)
            else:
                return
        else:
            # Traducir visual -> real
            idx_real = self._obtener_idx_real_de_visual(val_visual)
            self.guardar_respuesta_actual(idx_real)

    def _obtener_idx_real_de_visual(self, val_visual):
        # items_a_mostrar era lista de (idx_real, texto)
        # val_visual es base 1 (1, 2, 3...)
        items = self.mapa_respuestas_desordenadas[self.idx_pregunta]
        if 1 <= val_visual <= len(items):
            return items[val_visual-1][0] # El primer elemento de la tupla es idx_real
        return None

    def guardar_respuesta_actual(self, valor_real):
        # Guardar en la posición fija
        self.respuestas_usuario[self.idx_pregunta] = valor_real
        # Avanzar
        self.idx_pregunta += 1
        self.mostrar_pregunta()

    def pregunta_anterior(self):
        # Guardar lo que haya seleccionado actualmente al volver
        val_visual = self.resp_var.get()
        if val_visual != 0:
            idx_real = self._obtener_idx_real_de_visual(val_visual)
            self.respuestas_usuario[self.idx_pregunta] = idx_real
        
        if self.idx_pregunta > 0:
            self.idx_pregunta -= 1
            self.mostrar_pregunta()
            
    def saltar_a_pregunta(self, indice_destino):
        # Guardar actual antes de irse
        val_visual = self.resp_var.get()
        if val_visual != 0:
            idx_real = self._obtener_idx_real_de_visual(val_visual)
            self.respuestas_usuario[self.idx_pregunta] = idx_real
            
        if 0 <= indice_destino < self.cantidad:
            self.idx_pregunta = indice_destino
            self.mostrar_pregunta()

    # Reemplazo de métodos antiguos para compatibilidad si algo los llama
    def saltar_pregunta(self): 
        self.guardar_respuesta_actual(None)
    def siguiente_pregunta(self): 
        self.siguiente_pregunta_accion()
    def guardar_respuesta(self, x): 
        pass

    def mostrar_correccion(self):
        self.limpiar_ventana()

        # Calcular estadísticas
        aciertos, fallos, blancos = calcular_estadisticas(self.preguntas_seleccionadas, self.respuestas_usuario)
        nota = (aciertos / self.cantidad) * 10

        # Header Resumen
        header_frame = ttk.Frame(self.root, padding="15", relief="raised")
        header_frame.pack(fill="x")
        
        ttk.Label(header_frame, text="Resultados del Test", style="Title.TLabel").pack()
        
        resumen_frame = ttk.Frame(header_frame)
        resumen_frame.pack(pady=10)
        
        # Grid para stats
        ttk.Label(resumen_frame, text="NOTA FINAL", font=("Helvetica", 10)).grid(row=0, column=0, padx=20)
        ttk.Label(resumen_frame, text="ACIERTOS", font=("Helvetica", 10)).grid(row=0, column=1, padx=20)
        ttk.Label(resumen_frame, text="FALLOS", font=("Helvetica", 10)).grid(row=0, column=2, padx=20)
        ttk.Label(resumen_frame, text="BLANCOS", font=("Helvetica", 10)).grid(row=0, column=3, padx=20)
        
        color_nota = "green" if nota >= 5 else "red"
        ttk.Label(resumen_frame, text=f"{nota:.1f}", font=("Helvetica", 16, "bold"), foreground=color_nota).grid(row=1, column=0, padx=20)
        ttk.Label(resumen_frame, text=str(aciertos), font=("Helvetica", 14, "bold"), foreground="green").grid(row=1, column=1, padx=20)
        ttk.Label(resumen_frame, text=str(fallos), font=("Helvetica", 14, "bold"), foreground="red").grid(row=1, column=2, padx=20)
        ttk.Label(resumen_frame, text=str(blancos), font=("Helvetica", 14, "bold"), foreground="orange").grid(row=1, column=3, padx=20)


        # Lista de detalles con Scroll
        container = ttk.Frame(self.root, padding="10")
        container.pack(fill="both", expand=True)

        canvas = tk.Canvas(container, bg=self.bg_color, highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        window_id = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        
        def on_canvas_configure(event):
            canvas.itemconfig(window_id, width=event.width)
            
        def on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))

        canvas.bind("<Configure>", on_canvas_configure)
        scrollable_frame.bind("<Configure>", on_frame_configure)

        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Generar items
        for idx, (pregunta, resp) in enumerate(zip(self.preguntas_seleccionadas, self.respuestas_usuario), 1):
            generar_item_resultado(scrollable_frame, idx, pregunta, resp)

        # Scroll mouse
        def _on_mousewheel(event):
            try:
                canvas.yview_scroll(int(-1*(event.delta)), "units")
            except: pass

        # Vincular mousewheel solo cuando estamos en esta pantalla
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        self.current_mousewheel_bind = _on_mousewheel 
        
        # Botones de Acción (Guardar / Salir)
        action_frame = ttk.Frame(self.root, padding="10")
        action_frame.pack(fill="x", side="bottom")
        
        left_actions = ttk.Frame(action_frame)
        left_actions.pack(side="left")

        # ttk.Button(left_actions, text="💾 Guardar en Historial", command=lambda: self.guardar_en_db(nota, aciertos, fallos, blancos)).pack(side="left", padx=5)
        ttk.Button(left_actions, text="📄 Descargar Reporte", command=lambda: self.descargar_reporte(nota, aciertos, fallos, blancos)).pack(side="left", padx=5)

        # Guardado Automático
        self.guardar_en_db_automatico(nota, aciertos, fallos, blancos)

        # Derecha: Volver
        ttk.Button(action_frame, text="Volver al Menú", command=self.do_restart).pack(side="right", padx=5)

    def guardar_en_db_automatico(self, nota, aciertos, fallos, blancos):
        try:
            # Conexión DB en carpeta Documentos del usuario
            docs_dir = os.path.join(os.path.expanduser("~"), "Documents", "TestInteractivo")
            os.makedirs(docs_dir, exist_ok=True)
            db_path = os.path.join(docs_dir, "historial_test.db")
            
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            
            # Crear tabla si no existe
            c.execute('''CREATE TABLE IF NOT EXISTS intentos
                         (id INTEGER PRIMARY KEY AUTOINCREMENT,
                          fecha TEXT,
                          titulo TEXT,
                          nota REAL,
                          aciertos INTEGER,
                          fallos INTEGER,
                          blancos INTEGER,
                          detalles TEXT)''')

            # Determinar título automático
            # Usar nombre del primer archivo origen o "Mix"
            origen_base = "Test Personalizado"
            if self.preguntas_seleccionadas:
                origen_base = self.preguntas_seleccionadas[0].get('archivo_origen', '').replace('.csv', '').replace('_', ' ').capitalize()
            
            # Contar intentos previos de este tema para poner número
            c.execute("SELECT COUNT(*) FROM intentos WHERE titulo LIKE ?", (f"{origen_base}%",))
            num_intento = c.fetchone()[0] + 1
            
            titulo_final = f"{origen_base} - Intento {num_intento}"
            
            # Preparar datos
            fecha_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            detalles_json = json.dumps({
                "total_preguntas": self.cantidad,
                "respuestas_usuario": self.respuestas_usuario,
                "preguntas_info": [{
                    "pregunta": p.get('pregunta'),
                    "opciones": obtener_opciones(p),
                    "respuesta_correcta": int(p.get('respuesta', -1)),
                    "archivo_origen": p.get('archivo_origen')
                } for p in self.preguntas_seleccionadas]
            })
            
            c.execute("INSERT INTO intentos (fecha, titulo, nota, aciertos, fallos, blancos, detalles) VALUES (?, ?, ?, ?, ?, ?, ?)",
                      (fecha_str, titulo_final, nota, aciertos, fallos, blancos, detalles_json))
            
            conn.commit()
            conn.close()
            # Opcional: Notificar discreto o label
            # messagebox.showinfo("Auto-Guardado", f"Resultado guardado como: {titulo_final}")
            
        except Exception as e:
            print(f"Error Auto-Guardado: {e}")

    def ver_historial(self):
        self.limpiar_ventana()
        
        # Header Historial
        header_frame = ttk.Frame(self.root, padding="15")
        header_frame.pack(fill="x")
        ttk.Label(header_frame, text="Historial de Intentos", style="Title.TLabel").pack(side="left")
        ttk.Button(header_frame, text="Volver al Menú", command=self.do_restart).pack(side="right")
        
        # Treeview Lista
        tree_frame = ttk.Frame(self.root, padding="10")
        tree_frame.pack(fill="both", expand=True)
        
        cols = ("ID", "Fecha", "Título", "Nota", "Aciertos/Fallos")
        tree = ttk.Treeview(tree_frame, columns=cols, show="headings", selectmode="browse")
        
        tree.heading("ID", text="ID")
        tree.column("ID", width=40, anchor="center")
        tree.heading("Fecha", text="Fecha")
        tree.column("Fecha", width=150, anchor="center")
        tree.heading("Título", text="Test / Tema")
        tree.column("Título", width=300)
        tree.heading("Nota", text="Nota")
        tree.column("Nota", width=80, anchor="center")
        tree.heading("Aciertos/Fallos", text="Aciertos / Fallos")
        tree.column("Aciertos/Fallos", width=120, anchor="center")
        
        scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scroll.set)
        
        tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        
        # Bind MouseWheel for Treeview (macOS specific override if needed)
        def _on_tree_scroll(event):
            try:
                tree.yview_scroll(int(-1*(event.delta)), "units")
            except: pass
            
        # Bind to treeview explicitly and globally for safety
        tree.bind_all("<MouseWheel>", _on_tree_scroll)
        
        # Boton Ver Detalle
        btn_frame = ttk.Frame(self.root, padding="10")
        btn_frame.pack(fill="x")
        
        def ver_detalle_seleccionado():
            sel = tree.selection()
            if not sel: return
            item = tree.item(sel[0])
            id_intento = item['values'][0]
            self.cargar_detalle_historial(id_intento)

        ttk.Button(btn_frame, text="Ver Detalle del Intento", style="Action.TButton", command=ver_detalle_seleccionado).pack()

        # Cargar Datos DB
        try:
            docs_dir = os.path.join(os.path.expanduser("~"), "Documents", "TestInteractivo")
            db_path = os.path.join(docs_dir, "historial_test.db")
            
            if not os.path.exists(db_path):
                ttk.Label(tree_frame, text="No hay historial todavía.").pack()
                return

            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            c.execute("SELECT id, fecha, titulo, nota, aciertos, fallos FROM intentos ORDER BY id DESC")
            rows = c.fetchall()
            conn.close()
            
            for r in rows:
                # r = (id, fecha, titulo, nota, aciertos, fallos)
                fecha_fmt = r[1]
                stats = f"{r[4]} A / {r[5]} F"
                tree.insert("", "end", values=(r[0], fecha_fmt, r[2], f"{r[3]:.1f}", stats))
                
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo leer historial: {e}")


    def cargar_detalle_historial(self, id_intento):
        try:
            docs_dir = os.path.join(os.path.expanduser("~"), "Documents", "TestInteractivo")
            db_path = os.path.join(docs_dir, "historial_test.db")
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            c.execute("SELECT titulo, detalles FROM intentos WHERE id=?", (id_intento,))
            row = c.fetchone()
            conn.close()
            
            if not row: return
            
            titulo_test = row[0]
            detalles_str = row[1]
            data = json.loads(detalles_str)
            
            # Reconstruir estado para usar la vista de resultados existente
            # La vista 'mostrar_correccion' usa self.preguntas_seleccionadas y self.respuestas_usuario
            
            # Mapear JSON guardado a estructuras de objetos
            self.respuestas_usuario = data.get('respuestas') or data.get('respuestas_usuario')
            if not self.respuestas_usuario:
                 messagebox.showerror("Error", "Este registro antiguo no tiene respuestas guardadas.")
                 return

            raw_preguntas = data.get('preguntas_info')
            
            if raw_preguntas:
                # Formato nuevo rico (el que acabamos de crear en guardar_automatico)
                self.preguntas_seleccionadas = []
                for p in raw_preguntas:
                    # Reconstruir dict de pregunta
                    nueva_p = {
                        'pregunta': p['pregunta'],
                        'respuesta': p['respuesta_correcta'],
                        'archivo_origen': p.get('archivo_origen', '-')
                    }
                    # Opciones
                    ops = p['opciones']
                    if len(ops) >= 4:
                        nueva_p['opciona'] = ops[0]
                        nueva_p['opcionb'] = ops[1]
                        nueva_p['opcionc'] = ops[2]
                        nueva_p['opciond'] = ops[3]
                    self.preguntas_seleccionadas.append(nueva_p)
            else:
                # Formato antiguo (solo guardaba IDs o totales, no se puede reconstruir detalle visual completo sin las preguntas originales)
                # Si el DB guardaba las preguntas en otro lado, las necesitamos. 
                # El guardar_en_db antiguo guardaba: "total_preguntas" y "respuestas". No guardaba el texto de las preguntas.
                # CORRECCIÓN: El código anterior NO guardaba el texto de las preguntas en el JSON 'detalles', lo cual hace imposible
                # ver el detalle histórico si cambian los CSVs o no los cargamos.
                # He actualizado el guardar_automatico para incluir la info de la pregunta.
                # Para registros viejos, mostraremos aviso.
                messagebox.showwarning("Historial Antiguo", "Este registro es de una versión anterior y no contiene el texto de las preguntas para revisar.")
                return

            self.cantidad = len(self.preguntas_seleccionadas)
            
            # Usar la función existente para mostrar resultados
            # Pequeño hack: Modificar 'do_restart' del botón "Volver" en esa pantalla 
            # para que vuelva al historial en vez de al inicio, si queremos ser muy pro.
            # O simplemente dejar que vuelva al inicio.
            self.mostrar_correccion()
            
            # Cambiar título arriba para indicar que es histórico
            # (mostrar_correccion limpia la ventana, así que lo hacemos después o modificamos funcion)
            
        except Exception as e:
            messagebox.showerror("Error", f"Error cargando detalle: {e}")

    def guardar_en_db(self, nota, aciertos, fallos, blancos):
        titulo = simpledialog.askstring("Guardar Resultado", "Título para este intento (ej. 'Repaso Tema 1'):", parent=self.root)
        if not titulo: return
        
        try:
            # Conexión DB en carpeta Documentos del usuario
            docs_dir = os.path.join(os.path.expanduser("~"), "Documents", "TestInteractivo")
            os.makedirs(docs_dir, exist_ok=True)
            
            db_path = os.path.join(docs_dir, "historial_test.db")
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            
            # Crear tabla si no existe
            c.execute('''CREATE TABLE IF NOT EXISTS intentos
                         (id INTEGER PRIMARY KEY AUTOINCREMENT,
                          fecha TEXT,
                          titulo TEXT,
                          nota REAL,
                          aciertos INTEGER,
                          fallos INTEGER,
                          blancos INTEGER,
                          detalles TEXT)''')
            
            # Preparar datos
            fecha_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            detalles_json = json.dumps({
                "total_preguntas": self.cantidad,
                "respuestas": self.respuestas_usuario
            })
            
            c.execute("INSERT INTO intentos (fecha, titulo, nota, aciertos, fallos, blancos, detalles) VALUES (?, ?, ?, ?, ?, ?, ?)",
                      (fecha_str, titulo, nota, aciertos, fallos, blancos, detalles_json))
            
            conn.commit()
            conn.close()
            messagebox.showinfo("Éxito", f"Resultado guardado en historial.\nBase de datos: {db_path}")
            
        except Exception as e:
            messagebox.showerror("Error DB", f"No se pudo guardar: {e}")

    def descargar_reporte(self, nota, aciertos, fallos, blancos):
        # Preguntar título también para el reporte
        titulo = simpledialog.askstring("Reporte", "Título para el reporte:", initialvalue="Resultado Test", parent=self.root)
        if not titulo: titulo = "Resultado Test"
        
        fichero = filedialog.asksaveasfilename(defaultextension=".txt", 
                                             filetypes=[("Archivo de Texto", "*.txt"), ("Todos", "*.*")],
                                             initialfile=f"Reporte_{titulo}_{datetime.now().strftime('%Y%m%d')}.txt",
                                             title="Guardar Reporte")
        if not fichero: return
        
        try:
            with open(fichero, 'w', encoding='utf-8') as f:
                f.write(f"REPORTE DE TEST: {titulo}\n")
                f.write(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("="*40 + "\n")
                f.write(f"NOTA FINAL: {nota:.2f} / 10\n")
                f.write(f"Aciertos: {aciertos}\n")
                f.write(f"Fallos:   {fallos}\n")
                f.write(f"Blancos:  {blancos}\n")
                f.write("-" * 40 + "\n\n")
                
                f.write("DETALLE DE RESPUESTAS:\n")
                for i, (preg, resp) in enumerate(zip(self.preguntas_seleccionadas, self.respuestas_usuario), 1):
                    # Obtener info básica
                    txt_p = preg.get('pregunta', '???')
                    correcta = int(preg.get('respuesta', -1))
                    
                    try: 
                        opciones = obtener_opciones(preg) 
                    except: opciones = []
                    
                    def get_txt(idx):
                        if 1 <= idx <= len(opciones): return opciones[idx-1]
                        return "???"
                    
                    f.write(f"{i}. {txt_p}\n")
                    
                    if resp is None:
                        estado = "[NO CONTESTADA]"
                    elif resp == correcta:
                        estado = "[CORRECTA]"
                    else:
                        estado = f"[INCORRECTA] -> Tu respuesta: {get_txt(resp)}"
                        
                    f.write(f"   {estado}\n")
                    if resp != correcta:
                        f.write(f"   Respuesta Correcta: {get_txt(correcta)}\n")
                    f.write("\n")
                    
            messagebox.showinfo("Reporte Guardado", f"El reporte se ha guardado en:\n{fichero}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Fallo al guardar reporte: {e}")

    def do_restart(self):
         # Limpieza profunda de estado
         self.preguntas = []
         self.preguntas_seleccionadas = []
         self.respuestas_usuario = []
         self.mapa_respuestas_desordenadas = {} # CRÍTICO: Olvidar el orden aleatorio anterior
         self.idx_pregunta = 0
         self.cantidad = 0
         
         self.limpiar_bindings()
         self.setup_inicio()
         
    def limpiar_bindings(self):
        try:
            self.root.unbind_all("<MouseWheel>")
        except: pass

    def limpiar_ventana(self):
        self.limpiar_bindings()
        for widget in self.root.winfo_children():
            widget.destroy()

# --- Funciones Auxiliares Fuera de Clase ---

def cargar_preguntas_desde_archivos(archivos_csv):
    preguntas = []
    
    for archivo in archivos_csv:
        if not os.path.exists(archivo): continue
        nombre_fichero = os.path.basename(archivo)
        
        try:
            # Forzar utf-8-sig para borrar BOM automáticamente si existe
            # Forzar delimitador ';' duro, sin adivinar
            with open(archivo, 'r', encoding='utf-8-sig', errors='replace') as f:
                lector = csv.reader(f, delimiter=';')
                
                header_saltado = False
                
                for num_linea, fila in enumerate(lector, 1):
                    # Saltar filas vacías
                    if not fila: continue
                    
                    # Limpieza básica de espacios en cada campo
                    fila = [c.strip() for c in fila]
                    
                    # Detectar Header: Si la ultima columna es larga ("correcta" vs "a")
                    # o si la primera columna es literalmente "pregunta"
                    if not header_saltado:
                        if len(fila) > 0 and 'pregunta' in fila[0].lower():
                            header_saltado = True
                            continue
                        # Heurística extra: si la última columna tiene más de 1 char, es header
                        if len(fila) >= 6 and len(fila[-1]) > 1 and not fila[-1].isdigit(): 
                             header_saltado = True
                             continue

                    # Validación longitud mínima (Pregunta + 4 opciones + Correcta = 6 columnas)
                    if len(fila) < 6:
                        # Intento de rescate si faltan columnas vacías al final
                        while len(fila) < 6: fila.append("")
                    
                    # Extracción POSICIONAL (Independiente de nombres)
                    # 0: Pregunta
                    # 1: Opción A
                    # 2: Opción B
                    # 3: Opción C
                    # 4: Opción D
                    # 5: Respuesta Correcta
                    
                    pregunta_txt = fila[0]
                    opciones_raw = fila[1:5]
                    respuesta_raw = fila[5].upper()

                    # Decodificar respuesta (Letra o Número)
                    respuesta_idx = -1
                    if respuesta_raw.isdigit():
                        respuesta_idx = int(respuesta_raw)
                    elif len(respuesta_raw) == 1 and respuesta_raw >= 'A':
                         # Truco ASCII: 'A'(65) -> 1, 'B'(66) -> 2
                         respuesta_idx = ord(respuesta_raw) - 64
                    
                    # Guardar
                    preguntas.append({
                        'pregunta': pregunta_txt,
                        'opciona': opciones_raw[0],
                        'opcionb': opciones_raw[1],
                        'opcionc': opciones_raw[2],
                        'opciond': opciones_raw[3],
                        'respuesta': respuesta_idx,
                        'archivo_origen': nombre_fichero
                    })
                    
        except Exception as e:
            print(f"Error procesando archivo {nombre_fichero}: {e}")

    return preguntas

def detect_encoding(file_path):
    encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
    for enc in encodings:
        try:
            with open(file_path, 'r', encoding=enc) as f:
                f.read(4096)
            return enc
        except UnicodeDecodeError:
            continue
    return 'utf-8' # Fallback

def seleccionar_preguntas(preguntas, cantidad, mezclar_preguntas):
    import random
    selección = preguntas[:]
    if mezclar_preguntas:
        random.shuffle(selección)
    return selección[:cantidad]

def obtener_opciones(pregunta):
    return [
        pregunta.get('opciona', ''),
        pregunta.get('opcionb', ''),
        pregunta.get('opcionc', ''),
        pregunta.get('opciond', '')
    ]

def calcular_estadisticas(preguntas, respuestas):
    aciertos = 0
    fallos = 0
    blancos = 0
    
    for p, r in zip(preguntas, respuestas):
        try:
            correcta = int(p.get('respuesta', -1))
        except:
            correcta = -1
            
        if r is None:
            blancos += 1
        elif r == correcta:
            aciertos += 1
        else:
            fallos += 1
    return aciertos, fallos, blancos

def generar_item_resultado(parent, idx, pregunta, resp):
    # Frame para cada item
    frame = ttk.Frame(parent, padding="15", relief="solid", borderwidth=1)
    frame.pack(fill="x", padx=10, pady=5)
    
    # Datos
    try:
        correcta_idx = int(pregunta.get('respuesta', -1))
    except:
        correcta_idx = -1
        
    opciones = obtener_opciones(pregunta)
    
    # Determinar textos para mostrar
    def get_text_opcion(i):
        if 1 <= i <= len(opciones):
            return opciones[i-1]
        return f"Opción {i}"

    txt_tu_resp = "---"
    if resp is not None:
        txt_tu_resp = get_text_opcion(resp)
         
    txt_corr_resp = "Desconocida / Error en datos"
    if correcta_idx != -1:
        txt_corr_resp = get_text_opcion(correcta_idx)
        
    # Lógica Estado
    if resp is None:
        estado = "NO CONTESTADA"
        color_st = "orange"
        icon = "⏺"
    elif resp == correcta_idx:
        estado = "CORRECTA"
        color_st = "green"
        icon = "✔"
    else:
        estado = "INCORRECTA"
        color_st = "red"
        icon = "✖"
        
    # Layout del item
    
    # 1. Pregunta
    txt_preg = pregunta.get('pregunta', 'Sin enunciado')
    ttk.Label(frame, text=f"{idx}. {txt_preg}", font=("Helvetica", 11, "bold"), wraplength=700).pack(anchor="w", fill="x")
    
    # 2. Separador visual
    ttk.Separator(frame, orient="horizontal").pack(fill="x", pady=10)
    
    # 3. Datos Respuesta
    info_frame = ttk.Frame(frame)
    info_frame.pack(fill="x")
    
    # Estado (Izquierda)
    st_lbl = ttk.Label(info_frame, text=f"{icon} {estado}", font=("Helvetica", 10, "bold"), foreground=color_st)
    st_lbl.pack(anchor="w", pady=(0, 5))
    
    # Grid de detalles
    grid = ttk.Frame(info_frame)
    grid.pack(fill="x")
    
    ttk.Label(grid, text="Tu respuesta:", width=15, font=("Helvetica", 10, "bold"), foreground="#555").grid(row=0, column=0, sticky="nw")
    ttk.Label(grid, text=txt_tu_resp, wraplength=600, foreground="black" if resp == correcta_idx else "red").grid(row=0, column=1, sticky="w")
    
    ttk.Label(grid, text="Respuesta correcta:", width=15, font=("Helvetica", 10, "bold"), foreground="#555").grid(row=1, column=0, sticky="nw")
    ttk.Label(grid, text=txt_corr_resp, wraplength=600, foreground="blue").grid(row=1, column=1, sticky="w")
    
    # 4. Footer (Fuente)
    origen = pregunta.get('archivo_origen', '-')
    ttk.Label(frame, text=f"Fuente: {origen}", font=("Helvetica", 8), foreground="#999").pack(anchor="e", pady=(5,0))

if __name__ == "__main__":
    root = tk.Tk()
    app = TestApp(root)
    root.mainloop()

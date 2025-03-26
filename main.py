import tkinter as tk
from tkinter import filedialog, messagebox
import json
from pulp import *

def cargar_datos():
    """Carga los datos desde un archivo JSON."""
    archivo_ruta = filedialog.askopenfilename(filetypes=[("Archivos JSON", "*.json")])
    if archivo_ruta:
        try:
            with open(archivo_ruta, 'r') as archivo:
                datos = json.load(archivo)
            origen_entry.delete(0, tk.END)
            destino_entry.delete(0, tk.END)
            oferta_entry.delete(0, tk.END)
            demanda_entry.delete(0, tk.END)
            costo_entry.delete(0, tk.END)

            origen_entry.insert(0, ', '.join(datos['origen']))
            destino_entry.insert(0, ', '.join(datos['destino']))
            oferta_entry.insert(0, ', '.join(map(str, datos['oferta'])))
            demanda_entry.insert(0, ', '.join(map(str, datos['demanda'])))
            costo_entry.insert(0, ', '.join(map(str, datos['costo_envio'])))

        except FileNotFoundError:
            messagebox.showerror("Error", "Archivo no encontrado.")
        except json.JSONDecodeError:
            messagebox.showerror("Error", "Archivo JSON inválido.")
        except KeyError:
            messagebox.showerror("Error", "Estructura JSON incorrecta.")

def resolver_problema():
    """Resuelve el problema de transporte con los datos ingresados."""
    try:
        origenes = [o.strip() for o in origen_entry.get().split(',')]
        destinos = [d.strip() for d in destino_entry.get().split(',')]

        ofertas = [int(o.strip()) for o in oferta_entry.get().split(',')]
        demandas = [int(d.strip()) for d in demanda_entry.get().split(',')]
        costos = [int(c.strip()) for c in costo_entry.get().split(',')]

        # Validaciones
        if not all(origenes) or not all(destinos):
            raise ValueError("Los nombres de origen y destino no pueden estar vacíos.")
        if len(origenes) != len(ofertas):
            raise ValueError("El número de orígenes y ofertas debe coincidir.")
        if len(destinos) != len(demandas):
            raise ValueError("El número de destinos y demandas debe coincidir.")
        if len(costos) != len(origenes) * len(destinos):
            raise ValueError("El número de costos debe ser orígenes * destinos.")
        if any(o < 0 for o in ofertas) or any(d < 0 for d in demandas) or any(c < 0 for c in costos):
            raise ValueError("La oferta, demanda y costo deben ser valores no negativos.")

        oferta = {origenes[i]: ofertas[i] for i in range(len(origenes))}
        demanda = {destinos[i]: demandas[i] for i in range(len(destinos))}

        costo_envio = {}
        cost_index = 0
        for i in origenes:
            costo_envio[i] = {}
            for j in destinos:
                costo_envio[i][j] = costos[cost_index]
                cost_index += 1

        # Declaramos la función objetivo... nota que buscamos minimizar el costo (LpMinimize)
        prob = LpProblem('Transporte', LpMinimize)

        rutas = [(i, j) for i in origenes for j in destinos]
        cantidad = LpVariable.dicts('Cantidad de Envio', (origenes, destinos), 0)
        prob += lpSum(cantidad[i][j] * costo_envio[i][j] for (i, j) in rutas)
        for j in destinos:
            prob += lpSum(cantidad[i][j] for i in origenes) == demanda[j]
        for i in origenes:
            prob += lpSum(cantidad[i][j] for j in destinos) <= oferta[i]

        # Resolvemos e imprimimos el Status, si es Optimo, el problema tiene solución.
        prob.solve()
        resultado_text.delete(1.0, tk.END)  # Limpiar resultados anteriores
        resultado_text.insert(tk.END, "Estatus: " + LpStatus[prob.status] + "\n")

        # Imprimimos la solución
        for v in prob.variables():
            if v.varValue > 0:
                resultado_text.insert(tk.END, v.name.replace("_", " ") + " = " + str(v.varValue) + "\n")
        resultado_text.insert(tk.END, 'El costo mínimo es: ' + str(value(prob.objective)))

    except ValueError as e:
        messagebox.showerror("Error", str(e))
    except Exception as e:
        messagebox.showerror("Error", "Ocurrió un error inesperado: " + str(e))

# Interfaz Tkinter
ventana = tk.Tk()
ventana.title("Problema de Transporte")

# Botón para cargar archivo JSON
cargar_button = tk.Button(ventana, text="Cargar JSON", command=cargar_datos)
cargar_button.grid(row=0, column=0, columnspan=2)

# Etiquetas y campos de entrada
tk.Label(ventana, text="Orígenes (separados por comas):").grid(row=1, column=0)
origen_entry = tk.Entry(ventana)
origen_entry.grid(row=1, column=1)

tk.Label(ventana, text="Destinos (separados por comas):").grid(row=2, column=0)
destino_entry = tk.Entry(ventana)
destino_entry.grid(row=2, column=1)

tk.Label(ventana, text="Ofertas (separadas por comas):").grid(row=3, column=0)
oferta_entry = tk.Entry(ventana)
oferta_entry.grid(row=3, column=1)

tk.Label(ventana, text="Demandas (separadas por comas):").grid(row=4, column=0)
demanda_entry = tk.Entry(ventana)
demanda_entry.grid(row=4, column=1)

tk.Label(ventana, text="Costos de Envío (separados por comas):").grid(row=5, column=0)
costo_entry = tk.Entry(ventana)
costo_entry.grid(row=5, column=1)

# Botón para resolver
resolver_button = tk.Button(ventana, text="Resolver", command=resolver_problema)
resolver_button.grid(row=6, column=0, columnspan=2)

# Área de resultados
resultado_text = tk.Text(ventana, height=10, width=50)
resultado_text.grid(row=7, column=0, columnspan=2)

ventana.mainloop()
import tkinter as tk
from tkinter import ttk, messagebox
import libvirt
import sys

class VisorVM:
    def __init__(self, root):
        self.root = root
        self.root.title("Maquinas Virtuales")
        self.root.geometry("700x450")

        label_titulo = tk.Label(root, text="Maquinas Virtuales", font=("Arial", 16, "bold"))
        label_titulo.pack(pady=10)

        self.tabla = ttk.Treeview(root, columns=("Nombre", "Estado"), show='headings')
        self.tabla.heading("Nombre", text="Nombre de la VM")
        self.tabla.heading("Estado", text="Estado Actual")
        self.tabla.pack(pady=20, padx=20, fill="both", expand=True)

        frame_botones = tk.Frame(root)
        frame_botones.pack(pady=10)

        btn_crear = tk.Button(frame_botones, text="Nueva VM", command=self.ventana_crear, bg="green", fg="white", width=12)
        btn_crear.grid(row=0, column=0, padx=5)

        btn_iniciar = tk.Button(frame_botones, text="Iniciar", command=self.iniciar_vm, bg="blue", fg="white", width=12)
        btn_iniciar.grid(row=0, column=1, padx=5)

        btn_detener = tk.Button(frame_botones, text="Detener", command=self.detener_vm, bg="red", fg="white", width=12)
        btn_detener.grid(row=0, column=2, padx=5)

        try:
            self.conn = libvirt.open('qemu:///system')
            if self.conn is None:
                print('Fallo al conectar con el hipervisor')
                sys.exit(1)
        except libvirt.libvirtError as e:
            print(f'Error de conexión: {e}')
            sys.exit(1)
        self.actualizar_lista()
    
    def actualizar_lista(self):
        # 1. Limpiar tabla actual
        for i in self.tabla.get_children():
            self.tabla.delete(i)

        try:
            # 2. Obtener nombres de todas las máquinas virtuales
            # 'listAllDomains' nos da objetos que representan cada VM
            dominios = self.conn.listAllDomains()
            
            for dom in dominios:
                nombre = dom.name()
                estado_id, _ = dom.state()
                
                # Traducir el ID de estado a texto entendible
                estados = {
                    libvirt.VIR_DOMAIN_RUNNING: "Ejecutándose",
                    libvirt.VIR_DOMAIN_PAUSED: "Pausada",
                    libvirt.VIR_DOMAIN_SHUTOFF: "Apagada",
                    libvirt.VIR_DOMAIN_CRASHED: "Error"
                }
                estado_texto = estados.get(estado_id, "Desconocido")

                # 3. Insertar en la tabla de Tkinter
                self.tabla.insert("", "end", values=(nombre, estado_texto))
                
        except libvirt.libvirtError as e:
            messagebox.showerror("Error", f"No se pudo obtener la lista: {e}")

    def ventana_crear(self):
        messagebox.showinfo("Acción", "Aquí abriremos el formulario para crear la VM")

    def iniciar_vm(self):
        print("Intentando iniciar VM...")

    def detener_vm(self):
        print("Intentando detener VM...")


if __name__ == "__main__":
    root = tk.Tk()
    app = VisorVM(root)
    root.mainloop()